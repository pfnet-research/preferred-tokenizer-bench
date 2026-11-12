#!/usr/bin/env python3
"""Fetch bounded, reproducible review candidates, never marking them reviewed.

Uses the HF Dataset Viewer rows API; complete source rows and raw windows stay in
an explicitly chosen private cache. No model/API generation or bulk corpus fetch.
"""
import argparse
import bisect
import concurrent.futures
import hashlib
import json
from pathlib import Path
import random
import re
import time
import threading
import urllib.error
import urllib.parse
import urllib.request

BASE = Path(__file__).resolve().parents[1]
SOURCE_MIN = 2000
WINDOW_MIN = 1500
TARGET = 1000
SEED = 20261106
REQUEST_LOCK = threading.Lock()
NEXT_REQUEST = 0.0


def stable_seed(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str, parts)).encode()).digest()[:8], 'big')


def fetch_json(url, path):
    if path.exists():
        return json.loads(path.read_text())
    request = urllib.request.Request(url, headers={'User-Agent': 'preferred-tokenizer-bench/0.1 (bounded research sample)'})
    global NEXT_REQUEST
    for attempt in range(5):
        with REQUEST_LOCK:
            delay = NEXT_REQUEST - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            NEXT_REQUEST = time.monotonic() + 2.0
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read(8_000_001)
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            retry_after = error.headers.get('Retry-After', '65')
            try:
                delay = max(65, int(retry_after))
            except ValueError:
                delay = 65
            with REQUEST_LOCK:
                NEXT_REQUEST = max(NEXT_REQUEST, time.monotonic() + delay)
            print(json.dumps({'event': 'rate_limited', 'retry_after_seconds': delay}), flush=True)
    if len(payload) > 8_000_000:
        raise ValueError('API response exceeded 8 MB safety limit')
    result = json.loads(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False))
    return result


def rows_url(entry, offset, length):
    return 'https://datasets-server.huggingface.co/rows?' + urllib.parse.urlencode({
        'dataset': entry['dataset'], 'config': entry['config'], 'split': 'train',
        'offset': offset, 'length': length,
    })


def make_candidate(entry, source, index, row_idx, api_url, window_seed=SEED):
    text = source['text']
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode('utf-8')))
    total = offsets[-1]
    if total < SOURCE_MIN:
        return None
    rng = random.Random(stable_seed(window_seed, entry['tag'], source['id']))
    requested_start = rng.randrange(total - WINDOW_MIN + 1)
    start = bisect.bisect_left(offsets, requested_start)
    end = bisect.bisect_left(offsets, offsets[start] + WINDOW_MIN)
    if end > len(text):
        return None
    window = text[start:end]
    # Boundary proposals are algorithmic. A reviewer must read and approve them.
    prefix_limit = bisect.bisect_right(offsets, offsets[start] + 250) - start
    cuts = [m.end() for m in re.finditer(r'[.!?。！？\n]+\s*', window[:prefix_limit])]
    local_start = cuts[0] if cuts else 0
    possible_ends = []
    for match in re.finditer(r'[.!?。！？]+(?:["”’」』]?)(?=\s|$)|\n', window):
        candidate_end = match.end()
        size = len(window[local_start:candidate_end].strip().encode())
        if 700 <= size <= 1300:
            possible_ends.append((abs(size - TARGET), candidate_end))
    if possible_ends:
        local_end = min(possible_ends)[1]
    else:
        local_end = bisect.bisect_right(offsets, offsets[start + local_start] + TARGET) - 1 - start
        while local_end > local_start and not window[local_end - 1].isspace() and len(window[local_start:local_end].encode()) > 850:
            local_end -= 1
    while local_start < local_end and window[local_start].isspace():
        local_start += 1
    while local_end > local_start and window[local_end - 1].isspace():
        local_end -= 1
    excerpt = window[local_start:local_end]
    if len(excerpt.encode()) < 650:
        return None
    flags = []
    score = source.get('language_score')
    if score is not None and score < .8:
        flags.append('upstream_language_score_below_0.8')
    if entry['tag'] in ['zh-hans', 'zh-hant']:
        flags.append('requires_original_chinese_script_review')
    letters = [c for c in excerpt if c.isalpha()]
    latin = sum('a' <= c.lower() <= 'z' for c in letters)
    if entry['script'] not in ['Latn'] and letters and latin / len(letters) > .35:
        flags.append('substantial_ascii_latin_mixture')
    metadata = {
        'source': entry['dataset'], 'revision': entry['revision'],
        'config': entry['config'], 'split': 'train', 'url': source.get('url'),
        'file_path': source.get('file_path'), 'dump': source.get('dump'),
        'id': source['id'], 'date': source.get('date'),
        'language': source.get('language'), 'language_script': source.get('language_script'),
        'language_score': score, 'top_langs': source.get('top_langs'),
        'license': 'ODC-By-1.0', 'source_utf8_bytes': total,
        'source_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'sampling_seed': window_seed, 'api_url': api_url, 'api_row_index': row_idx,
        'window_start_char': start, 'window_end_char': end,
        'window_start_utf8_byte': offsets[start], 'window_end_utf8_byte': offsets[end],
        'window_utf8_bytes': len(window.encode()),
        'excerpt_start_char': start + local_start,
        'excerpt_end_char': start + local_end,
        'review_status': 'pending', 'review_flags': flags,
        'boundary_method': 'automatic proposal; requires reading and approval',
    }
    return {
        'id': f"fineweb-{entry['tag']}-{index:04d}", 'text': excerpt,
        'metadata': metadata,
    }, {'source': source, 'random_window': window}


def sample_entry(entry, cache, max_pages=8, target=50):
    tag = entry['tag']
    directory = cache / tag
    directory.mkdir(parents=True, exist_ok=True)
    status = {'tag': tag, 'config': entry['config'], 'dataset': entry['dataset'],
              'target': target, 'candidates': 0, 'reviewed': 0, 'rejections': {}, 'errors': []}
    candidates = []
    private = []
    seen = set()
    candidate_path = directory / 'candidates.jsonl'
    proof_path = directory / 'private-proof.jsonl'
    if candidate_path.exists() and proof_path.exists():
        candidates = [json.loads(line) for line in candidate_path.read_text().splitlines()]
        private = [json.loads(line) for line in proof_path.read_text().splitlines()]
        seen = {row['metadata']['id'] for row in candidates}
        if len(candidates) >= target and (directory / 'status.json').exists():
            return json.loads((directory / 'status.json').read_text())
    try:
        total = entry.get('train_documents')
        if not total:
            initial = fetch_json(rows_url(entry, 0, 1), directory / 'metadata-row.json')
            total = initial['num_rows_total']
        status['source_train_documents'] = total
        rng = random.Random(stable_seed(SEED, tag, entry['config']))
        offsets = [rng.randrange(max(1, total - 99)) for _ in range(max_pages)]
        if total <= 800:
            # Read a bounded complete tiny partition in shuffled page order.
            offsets = list(range(0, total, 100))
            rng.shuffle(offsets)
        for offset in offsets:
            url = rows_url(entry, offset, min(100, total - offset))
            try:
                response = fetch_json(url, directory / f'rows-{offset}.json')
            except urllib.error.HTTPError as error:
                if error.code in (500, 502, 503, 504):
                    status['errors'].append(f'block offset {offset}: HTTP {error.code}')
                    continue
                raise
            status['response_partial'] = bool(response.get('partial'))
            block_rows = list(response['rows'])
            rng.shuffle(block_rows)
            for item in block_rows:
                source = item['row']
                source_id = source.get('id')
                if not source_id or source_id in seen:
                    continue
                seen.add(source_id)
                if 'text' in item.get('truncated_cells', []):
                    status['rejections']['api_truncated_text'] = status['rejections'].get('api_truncated_text', 0) + 1
                    continue
                if len(source.get('text', '').encode()) < SOURCE_MIN:
                    status['rejections']['source_under_2000_bytes'] = status['rejections'].get('source_under_2000_bytes', 0) + 1
                    continue
                candidate = make_candidate(entry, source, len(candidates) + 1, item['row_idx'], url)
                if candidate is None:
                    continue
                row, proof = candidate
                candidates.append(row)
                private.append({'id': row['id'], **proof})
                if len(candidates) >= target:
                    break
            if len(candidates) >= target:
                break
        status.update(candidates=len(candidates), scanned_unique_documents=len(seen),
                      status='pending_review' if len(candidates) >= target else ('fetch_partial_error' if status['errors'] else 'shortfall_pending_review'))
    except Exception as error:
        status.update(status='fetch_error', errors=[str(error)])
    status['candidates'] = len(candidates)
    for name, values in [('private-proof.jsonl', private), ('candidates.jsonl', candidates)]:
        temporary = directory / (name + '.tmp')
        temporary.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values))
        temporary.replace(directory / name)
    (directory / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--languages', help='comma-separated tags; default all')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--max-pages', type=int, default=8)
    parser.add_argument('--target-candidates', type=int, default=50)
    args = parser.parse_args()
    entries = json.loads((BASE / 'dataset/languages.json').read_text())['languages']
    if args.languages:
        ordered_tags = args.languages.split(',')
        wanted = set(ordered_tags)
        assert len(ordered_tags) == len(wanted), 'duplicate requested tags'
        entry_by_tag = {e['tag']: e for e in entries}
        assert wanted <= entry_by_tag.keys(), 'unknown requested language'
        entries = [entry_by_tag[tag] for tag in ordered_tags]
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(sample_entry, e, args.cache_dir, args.max_pages, args.target_candidates) for e in entries]
        statuses = []
        for future in concurrent.futures.as_completed(futures):
            status = future.result()
            statuses.append(status)
            print(json.dumps(status, ensure_ascii=False), flush=True)
    (args.cache_dir / 'sampling-report.json').write_text(json.dumps(statuses, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
