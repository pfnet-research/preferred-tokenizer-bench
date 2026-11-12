#!/usr/bin/env python3
"""Apply explicit reading decisions to private FineWeb candidates.

This program never makes a review decision. A reviewer supplies source-character
spans after reading the actual source/window, confirming language and boundaries.
Only T4/T5 approved excerpts can be exported; T1-T3 require independent originals.
"""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def apply_decision(candidate, proof, decision):
    assert candidate['id'] == proof['id'] == decision['id']
    assert decision['action'] in ('approve', 'reject')
    if decision['action'] == 'reject':
        return None
    assert decision.get('language_confirmed') is True
    assert decision.get('boundaries_reviewed') is True
    assert decision.get('reviewer') and decision.get('reviewed_at')
    source = proof['source']['text']
    meta = candidate['metadata']
    assert hashlib.sha256(source.encode()).hexdigest() == meta['source_sha256']
    spans = decision.get('source_character_spans') or [[meta['excerpt_start_char'], meta['excerpt_end_char']]]
    previous = -1
    pieces = []
    for start, end in spans:
        assert meta['window_start_char'] <= start < end <= meta['window_end_char']
        assert previous <= start
        previous = end
        pieces.append(source[start:end])
    text = '\n'.join(pieces)
    assert 600 <= len(text.encode()) <= 1500, 'reviewed excerpt should be about 1000 UTF-8 bytes'
    approved = {'id': candidate['id'], 'text': text, 'metadata': dict(meta)}
    approved['metadata'].update(
        review_status='reviewed', reviewed_by=decision['reviewer'],
        reviewed_at=decision['reviewed_at'], source_character_spans=spans,
        language_confirmed=True, boundaries_reviewed=True,
        review_notes=decision.get('notes', ''),
        boundary_method='explicit source-character spans approved after reading',
    )
    return approved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--language', required=True)
    args = parser.parse_args()
    manifest = json.loads((BASE / 'dataset/languages.json').read_text())
    entry = next(e for e in manifest['languages'] if e['tag'] == args.language)
    assert entry['output_kind'] == 'excerpt', 'T1-T3 must be written as independent originals'
    directory = args.cache_dir / args.language
    candidates = {r['id']: r for r in map(json.loads, (directory / 'candidates.jsonl').read_text().splitlines())}
    proof = {r['id']: r for r in map(json.loads, (directory / 'private-proof.jsonl').read_text().splitlines())}
    decisions = list(map(json.loads, args.decisions.read_text().splitlines()))
    assert len({d['id'] for d in decisions}) == len(decisions), 'duplicate decisions'
    approved = []
    for decision in decisions:
        row = apply_decision(candidates[decision['id']], proof[decision['id']], decision)
        if row is not None:
            approved.append(row)
    approved.sort(key=lambda r: r['id'])
    output = BASE / 'dataset/fineweb' / (args.language + '.jsonl')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.jsonl.tmp')
    temporary.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in approved))
    temporary.replace(output)
    print(json.dumps({'language': args.language, 'reviewed': len(decisions), 'approved': len(approved), 'output': str(output)}))


if __name__ == '__main__':
    main()
