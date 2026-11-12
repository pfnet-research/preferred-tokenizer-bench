#!/usr/bin/env python3
"""Bounded fallback for Dataset Viewer errors (optional pyarrow dependency).

Only explicitly requested partitions are fetched; files over 64 MB are refused.
This is a small source-file sample, not uniform sampling of the complete corpus.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import urllib.parse
import urllib.request

from sample_fineweb import BASE, SEED, fetch_json, make_candidate, stable_seed


def sample(entry, cache, split, target=50):
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise SystemExit('Install optional pyarrow into a local virtual environment.') from error
    dataset = entry['dataset']
    revision = entry['revision']
    config = entry['config']
    directory = cache / entry['tag']
    directory.mkdir(parents=True, exist_ok=True)
    tree_url = f'https://huggingface.co/api/datasets/{dataset}/tree/{revision}/data/{config}/{split}'
    tree = fetch_json(tree_url, directory / f'parquet-tree-{split}.json')
    files = [item for item in tree if item['path'].endswith('.parquet')]
    assert files, 'no parquet files'
    rng = random.Random(stable_seed(SEED, entry['tag'], config, 'bounded_parquet_fallback'))
    file = rng.choice(files)
    assert file['size'] <= 64_000_000, 'bounded fallback refuses source files over 64 MB'
    source_file = directory / (split + '-' + Path(file['path']).name)
    url = f'https://huggingface.co/datasets/{dataset}/resolve/{revision}/{file["path"]}'
    if not source_file.exists():
        temporary = source_file.with_suffix('.partial')
        with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
            transferred = 0
            while chunk := response.read(1024 * 1024):
                transferred += len(chunk)
                assert transferred <= 64_000_000
                output.write(chunk)
        assert temporary.stat().st_size == file['size']
        temporary.replace(source_file)
    assert source_file.stat().st_size == file['size']
    sources = list(enumerate(pq.read_table(source_file).to_pylist()))
    rng.shuffle(sources)
    candidate_path = directory / 'candidates.jsonl'
    proof_path = directory / 'private-proof.jsonl'
    candidates = [json.loads(line) for line in candidate_path.read_text().splitlines()] if candidate_path.exists() else []
    proof = [json.loads(line) for line in proof_path.read_text().splitlines()] if proof_path.exists() else []
    if len(candidates) >= target:
        print(json.dumps({'tag': entry['tag'], 'candidates': len(candidates), 'status': 'existing_pool_preserved'}), flush=True)
        return
    existing_ids = {row['metadata']['id'] for row in candidates}
    rejected = 0
    scanned = 0
    for scanned, (row_index, source) in enumerate(sources, 1):
        if source['id'] in existing_ids:
            continue
        if len(source.get('text', '').encode()) < 2000:
            rejected += 1
            continue
        result = make_candidate(entry, source, len(candidates) + 1, row_index, url)
        if result is None:
            continue
        row, private = result
        row['metadata'].update(split=split, sampling_method='seeded shuffle of bounded source parquet',
                               source_parquet=file['path'])
        candidates.append(row)
        existing_ids.add(source['id'])
        proof.append({'id': row['id'], **private})
        if len(candidates) >= target:
            break
    for name, rows in [('candidates.jsonl', candidates), ('private-proof.jsonl', proof)]:
        (directory / name).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    status = {'tag': entry['tag'], 'config': config, 'dataset': dataset, 'target': target,
              'candidates': len(candidates), 'reviewed': 0, 'source_documents': len(sources),
              'status': 'pending_review' if len(candidates) >= target else 'shortfall_pending_review',
              'source_split': split, 'fallback_parquet_bytes': file['size'],
              'source_parquet': file['path'], 'scanned_documents': scanned,
              'rejections': {'source_under_2000_bytes': rejected}, 'errors': []}
    (directory / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(status, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--languages', required=True)
    parser.add_argument('--split', choices=['train', 'test'], default='train')
    parser.add_argument('--target-candidates', type=int, default=50)
    args = parser.parse_args()
    wanted = set(args.languages.split(','))
    entries = [e for e in json.loads((BASE / 'dataset/languages.json').read_text())['languages'] if e['tag'] in wanted]
    assert len(entries) == len(wanted)
    for entry in entries:
        sample(entry, args.cache_dir, args.split, args.target_candidates)


if __name__ == '__main__':
    main()
