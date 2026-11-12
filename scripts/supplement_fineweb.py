#!/usr/bin/env python3
"""Append distinct-document candidates from a pinned, bounded older FW2 file.

Existing candidate IDs, source proofs and reviewed output files are preserved.
The older filtered revision must be stated explicitly; it is never relabeled as
current data. Optional pyarrow is needed only for this acquisition operation.
"""
import argparse
import json
from pathlib import Path
import random
import urllib.request

from sample_fineweb import BASE, fetch_json, make_candidate, stable_seed


def append_sources(entry, sources, candidates, proofs, source_url, source_path):
    existing_ids = {row['metadata']['id'] for row in candidates}
    appended = []
    for row_index, source in sources:
        if source['id'] in existing_ids or len(source.get('text', '').encode()) < 2000:
            continue
        result = make_candidate(entry, source, len(candidates) + 1, row_index, source_url)
        if result is None:
            continue
        row, proof = result
        row['metadata'].update(source_parquet=source_path, split='train',
                               sampling_method='distinct-document supplement from bounded older filtered parquet')
        candidates.append(row)
        proofs.append({'id': row['id'], **proof})
        existing_ids.add(source['id'])
        appended.append(row['id'])
    return appended


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', required=True, type=Path)
    parser.add_argument('--languages', required=True)
    parser.add_argument('--revision', required=True, help='immutable source commit SHA')
    parser.add_argument('--max-file-bytes', type=int, default=1_000_000)
    args = parser.parse_args()
    assert len(args.revision) == 40 and all(c in '0123456789abcdef' for c in args.revision)
    import pyarrow.parquet as pq
    entries = {e['tag']: e for e in json.loads((BASE / 'dataset/languages.json').read_text())['languages']}
    for tag in args.languages.split(','):
        entry = dict(entries[tag], revision=args.revision)
        assert entry['dataset'] == 'HuggingFaceFW/fineweb-2'
        directory = args.cache_dir / tag
        candidates = [json.loads(line) for line in (directory / 'candidates.jsonl').read_text().splitlines()]
        proofs = [json.loads(line) for line in (directory / 'private-proof.jsonl').read_text().splitlines()]
        tree_url = f'https://huggingface.co/api/datasets/{entry["dataset"]}/tree/{args.revision}/data/{entry["config"]}/train'
        tree = fetch_json(tree_url, directory / f'supplement-tree-{args.revision}.json')
        files = [f for f in tree if f['path'].endswith('.parquet')]
        additions = []
        for info in files:
            assert info['size'] <= args.max_file_bytes, 'supplement would exceed the explicit bounded-file limit'
            cache_file = directory / f'supplement-{args.revision}-{Path(info["path"]).name}'
            url = f'https://huggingface.co/datasets/{entry["dataset"]}/resolve/{args.revision}/{info["path"]}'
            if not cache_file.exists():
                with urllib.request.urlopen(url, timeout=45) as response:
                    payload = response.read(args.max_file_bytes + 1)
                assert len(payload) == info['size'] <= args.max_file_bytes
                cache_file.write_bytes(payload)
            sources = list(enumerate(pq.read_table(cache_file).to_pylist()))
            random.Random(stable_seed(args.revision, tag, 'supplement')).shuffle(sources)
            additions.extend(append_sources(entry, sources, candidates, proofs, url, info['path']))
        for name, rows in [('private-proof.jsonl', proofs), ('candidates.jsonl', candidates)]:
            temporary = directory / (name + '.tmp')
            temporary.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            temporary.replace(directory / name)
        status = json.loads((directory / 'status.json').read_text())
        status['candidates'] = len(candidates)
        status['status'] = 'pending_review'
        supplemental = status.setdefault('supplemental_sources', [])
        if not any(item['revision'] == args.revision for item in supplemental):
            supplemental.append({'revision': args.revision, 'config': entry['config'],
                                 'split': 'train', 'appended_candidate_ids': additions,
                                 'all_source_files_scanned': True})
        (directory / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'tag': tag, 'source_revision': args.revision, 'added': len(additions),
                          'candidate_total': len(candidates), 'appended_ids': additions}, ensure_ascii=False))


if __name__ == '__main__':
    main()
