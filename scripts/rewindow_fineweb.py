#!/usr/bin/env python3
"""Append explicitly logged random-window retries for unapproved source docs."""
import argparse
import hashlib
import json
from pathlib import Path

from sample_fineweb import BASE, SEED, make_candidate, stable_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--language', required=True)
    parser.add_argument('--from-candidates', required=True)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--reason', required=True)
    args = parser.parse_args()
    assert 1 <= args.attempt <= 3, 'bounded, explicit retries only'
    directory = args.cache_dir / args.language
    rows = [json.loads(line) for line in (directory / 'candidates.jsonl').read_text().splitlines()]
    proofs = [json.loads(line) for line in (directory / 'private-proof.jsonl').read_text().splitlines()]
    by_id = {r['id']: r for r in rows}
    proof_by_id = {r['id']: r for r in proofs}
    approved_path = BASE / 'dataset/fineweb' / (args.language + '.jsonl')
    approved_ids = {json.loads(line)['metadata']['id'] for line in approved_path.read_text().splitlines()} if approved_path.exists() else set()
    manifest = json.loads((BASE / 'dataset/languages.json').read_text())['languages']
    baseline = next(e for e in manifest if e['tag'] == args.language)
    added = []
    for original_id in args.from_candidates.split(','):
        if any(r['metadata'].get('rewindow_from_candidate') == original_id and r['metadata'].get('window_retry_attempt') == args.attempt for r in rows):
            continue
        original = by_id[original_id]
        meta = original['metadata']
        assert meta['id'] not in approved_ids, 'cannot count a second window of an already approved original document'
        source = proof_by_id[original_id]['source']
        assert hashlib.sha256(source['text'].encode()).hexdigest() == meta['source_sha256']
        seed = stable_seed(SEED, 'window-retry', original_id, args.attempt) % (2 ** 32)
        entry = dict(baseline, dataset=meta['source'], revision=meta['revision'], config=meta['config'])
        result = make_candidate(entry, source, len(rows) + 1, meta['api_row_index'], meta['api_url'], window_seed=seed)
        if result is None:
            added.append({'from_candidate': original_id, 'attempt': args.attempt, 'seed': seed, 'result': 'automatic_proposal_unavailable'})
            continue
        row, private = result
        for field in ['source_parquet', 'split']:
            if field in meta:
                row['metadata'][field] = meta[field]
        row['metadata'].update(rewindow_from_candidate=original_id, window_retry_attempt=args.attempt,
                               window_retry_reason=args.reason, document_sampling_seed=meta.get('document_sampling_seed', meta['sampling_seed']),
                               window_seed_derivation='stable_seed(20261106, window-retry, original_candidate_id, attempt) modulo 2^32')
        rows.append(row)
        proofs.append({'id': row['id'], **private})
        added.append({'id': row['id'], 'from_candidate': original_id, 'attempt': args.attempt, 'seed': seed, 'original_source_id': meta['id']})
    for name, values in [('private-proof.jsonl', proofs), ('candidates.jsonl', rows)]:
        temp = directory / (name + '.tmp')
        temp.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values))
        temp.replace(directory / name)
    status = json.loads((directory / 'status.json').read_text())
    status['candidates'] = len(rows)
    status['distinct_original_document_ids'] = len({r['metadata']['id'] for r in rows})
    status.setdefault('explicit_window_retries', []).extend(added)
    (directory / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(added, ensure_ascii=False))


if __name__ == '__main__':
    main()
