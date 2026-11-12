#!/usr/bin/env python3
"""Validate saved dataset rows; --require-complete also requires every target."""
import argparse
import collections
import json
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def validate(require_complete=False):
    languages = json.loads((BASE / 'dataset/languages.json').read_text())['languages']
    assert len(languages) == 149
    assert len({e['tag'] for e in languages}) == 149
    assert collections.Counter(e['tier'] for e in languages) == {'T1': 2, 'T2': 3, 'T3': 12, 'T4': 36, 'T5': 96}
    entries = {e['tag']: e for e in languages}
    ids = set()
    file_counts = {}
    for path in sorted((BASE / 'dataset').glob('*/*.jsonl')):
        count = 0
        source_ids = set()
        source_hashes = set()
        document_texts = set()
        for line_no, line in enumerate(path.read_text(encoding='utf-8', errors='strict').splitlines(), 1):
            row = json.loads(line)
            assert set(row) == {'id', 'text', 'metadata'}, (path, line_no)
            assert isinstance(row['id'], str) and row['id'] and row['id'] not in ids
            ids.add(row['id'])
            assert isinstance(row['text'], str) and row['text']
            assert row['text'] not in document_texts, (path, 'duplicate full text')
            document_texts.add(row['text'])
            meta = row['metadata']
            assert isinstance(meta, dict)
            if path.parent.name == 'characters':
                assert len(row['text']) == 1
                assert meta['collection_offset'] == line_no - 1
                assert meta['codepoint'] == f"U+{ord(row['text']):04X}"
            elif path.parent.name != 'fineweb':
                assert meta == {'source': 'original'}, (path, line_no)
            else:
                entry = entries[path.stem]
                assert row['id'].startswith('fineweb-' + path.stem + '-')
                if entry['output_kind'] == 'original':
                    assert meta == {'source': 'original'}
                else:
                    assert meta.get('review_status') == 'reviewed', 'pending candidates cannot enter dataset/fineweb'
                    assert meta.get('language_confirmed') is True and meta.get('boundaries_reviewed') is True
                    assert meta.get('reviewed_by') and meta.get('reviewed_at')
                    assert meta['source_utf8_bytes'] >= 2000 and meta['window_utf8_bytes'] >= 1500
                    assert meta['url'] and meta['file_path'] and meta['dump'] and meta['id']
                    assert meta['source'] == entry['dataset'] and meta['config'] == entry['config']
                    assert meta['revision'] in [entry['revision'], *entry.get('supplemental_source_revisions', [])]
                    assert meta['id'] not in source_ids and meta['source_sha256'] not in source_hashes
                    source_ids.add(meta['id'])
                    source_hashes.add(meta['source_sha256'])
                    assert meta['revision'] and meta['source_sha256']
                    assert 600 <= len(row['text'].encode()) <= 1500
            count += 1
        file_counts[str(path.relative_to(BASE))] = count
    character_manifest = json.loads((BASE / 'dataset/characters/manifest.json').read_text())
    for collection in character_manifest['collections'].values():
        path = BASE / 'dataset/characters' / collection['file']
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        assert len(rows) == collection['documents']
        assert len(raw) == collection['jsonl_bytes']
        assert hashlib.sha256(raw).hexdigest() == collection['jsonl_sha256']
        text = ''.join(row['text'] for row in rows)
        assert hashlib.sha256(text.encode()).hexdigest() == collection['concatenated_text_sha256']
    missing = []
    for entry in languages:
        path = 'dataset/fineweb/' + entry['tag'] + '.jsonl'
        count = file_counts.get(path, 0)
        if count != 50:
            missing.append({'tag': entry['tag'], 'saved': count, 'target': 50})
    for genre in ('news', 'sns', 'code', 'academic'):
        for language in ('ja', 'en'):
            path = f'dataset/{genre}/{language}.jsonl'
            if file_counts.get(path, 0) != 50:
                missing.append({'path': path, 'saved': file_counts.get(path, 0), 'target': 50})
    if require_complete:
        assert not missing, f'incomplete targets: {missing}'
    result = {'rows': len(ids), 'files': file_counts, 'incomplete_targets': missing,
              'complete': not missing, 'status': 'complete' if not missing else 'partial'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    validate(args.require_complete)
