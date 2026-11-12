#!/usr/bin/env python3
"""Flag representative production-meta annotations for contextual review.

This is a review aid, not a forbidden-word assertion. Technical hypotheses,
simulations, limitations and discussion of fiction are legitimate subject matter.
The representative patterns do not replace full multilingual contextual review.
"""
import argparse
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
PATTERNS = {
    'prefixed_origin_label': r'^\s*\[(?:Fiksi|Finzione|Fiction(?:al)?|架空|虚构|虛構|허구)\]',
    'explicit_origin_statement': r'\b(?:this|the) (?:story|article|example|dataset|study|account) is (?:entirely )?(?:fictional|invented|synthetic|made.up)\b',
    'production_safety_aside': r'\b(?:not (?:a |an )?certification|no actual participants|no real (?:seeds|patients|participants|treatments) (?:are|were)|all numerical values are (?:fabricated|invented))\b',
    'japanese_origin_aside': r'これは(?:架空|仮想|創作|例示用)|実在の(?:人物|組織|団体).{0,24}(?:無関係|関係ありません)',
}
COMPILED = {name: re.compile(pattern, re.IGNORECASE | re.MULTILINE) for name, pattern in PATTERNS.items()}


def scan_text(text):
    hits = []
    for name, pattern in COMPILED.items():
        for match in pattern.finditer(text):
            hits.append({'kind': name, 'start': match.start(), 'end': match.end(),
                         'context': text[max(0, match.start()-90):match.end()+140]})
    return sorted(hits, key=lambda hit: (hit['start'], hit['kind']))


def scan_dataset(base=BASE):
    reviewed = 0
    candidates = []
    for path in sorted((base / 'dataset').glob('*/*.jsonl')):
        for row in map(json.loads, path.read_text().splitlines()):
            if row['metadata'] != {'source': 'original'}:
                continue
            reviewed += 1
            hits = scan_text(row['text'])
            if hits:
                candidates.append({'file': str(path.relative_to(base)), 'id': row['id'], 'hits': hits})
    return {'scope': 'Original rows only; candidates require contextual judgment, not automatic deletion.',
            'documents_scanned': reviewed, 'candidate_documents': len(candidates), 'candidates': candidates}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = scan_dataset()
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
        print(json.dumps({k: v for k, v in result.items() if k != 'candidates'}))
    else:
        print(text, end='')
