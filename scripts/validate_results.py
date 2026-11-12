#!/usr/bin/env python3
"""Validate result/corpus identity, totals, artifacts and common sample evidence."""
import argparse
import json
import math
from pathlib import Path

from evaluate_tokenizers import VOCAB_SIZE_DEFINITION, BASE, SEED, load_corpus, metric, select_examples


def validate(output, allow_partial=False):
    rows, corpus = load_corpus()
    assert corpus['complete'] or allow_partial, 'Current corpus is unfinished.'
    selected, selection_sha = select_examples(rows)
    if corpus['complete']:
        assert len(rows) == 17595 and len(selected) == 346
    index = json.loads((output / 'index.json').read_text())
    assert index['schema_version'] == 1
    assert index['corpus'] == corpus, 'Result index does not identify the current corpus exactly.'
    assert index['selection_sha256'] == selection_sha and index['sample_documents'] == len(selected)
    assert index['sample_seed'] == SEED
    manifest = json.loads((BASE / 'dataset/tokenizers.json').read_text())['tokenizers']
    entries = {e['slug']: e for e in manifest}
    assert {e['slug'] for e in index['tokenizers']} == set(entries)
    assert entries and all(e['backend'] in ('huggingface', 'tiktoken', 'grok-tiktoken') for e in entries.values())
    assert {p.parent.name for p in output.glob('*/summary.json')} == set(entries), 'Unregistered result directory remains.'
    assert {p.name for p in (output / 'pages').iterdir() if p.is_dir()} == set(entries), 'Unregistered report directory remains.'
    natural = [r for r in rows if r['category'] != 'characters']
    characters = [r for r in rows if r['category'] == 'characters']
    assert len(characters) == 9745
    if corpus['complete']:
        assert len(natural) == 7850
    expected_chars = sum(len(r['text']) for r in natural)
    expected_bytes = sum(len(r['text'].encode()) for r in natural)
    package_versions = None
    for item in index['tokenizers']:
        slug = item['slug']
        summary = json.loads((output / item['summary_path']).read_text())
        examples = json.loads((output / item['examples_path']).read_text())
        assert summary['tokenizer'] == entries[slug]
        assert summary['corpus'] == corpus
        assert summary['selection_sha256'] == selection_sha
        assert examples['corpus_sha256'] == corpus['sha256']
        assert examples['selection_sha256'] == selection_sha and examples['seed'] == SEED
        metrics = summary['metrics']
        assert item['vocab_size'] == summary['vocab_size']
        assert type(item['vocab_size']) is int and item['vocab_size'] > 0
        assert item['vocab_size_metadata'] == summary['vocab_size_metadata']
        vocabulary = summary['vocab_size_metadata']
        assert vocabulary['definition'] == VOCAB_SIZE_DEFINITION
        assert type(vocabulary['id_capacity']) is int and vocabulary['id_capacity'] >= item['vocab_size']
        assert item['metrics'] == metrics
        assert metrics['documents'] == len(natural)
        assert metrics['characters'] == expected_chars and metrics['utf8_bytes'] == expected_bytes
        assert metrics['tokens'] > 0
        assert math.isclose(metrics['bytes_per_token'], expected_bytes / metrics['tokens'])
        assert math.isclose(metrics['chars_per_token'], expected_chars / metrics['tokens'])
        for group in ('collections', 'groups'):
            assert sum(m['tokens'] for m in summary[group].values()) == metrics['tokens']
            assert sum(m['documents'] for m in summary[group].values()) == len(natural)
        assert sum(v['total'] for v in summary['character_coverage'].values()) == 9745
        for value in summary['character_coverage'].values():
            assert 0 <= value['one_token'] <= value['total']
            assert math.isclose(value['ratio'], value['one_token'] / value['total'])
        assert summary['external_normalization'] == 'none; original Unicode text and whitespace passed unchanged'
        if package_versions is None:
            package_versions = summary['package_versions']
        assert summary['package_versions'] == package_versions
        declared = {f['path']: f for f in entries[slug]['files']}
        assert {f['path'] for f in summary['artifacts']} == set(declared)
        for actual in summary['artifacts']:
            assert actual['sha256'] == declared[actual['path']]['sha256']
            assert actual['bytes'] == declared[actual['path']]['size']
        assert item['ranking_eligible'] is True
        fidelity = summary['fidelity']
        assert fidelity['documents'] == len(natural)
        assert fidelity.get('roundtrip_exact_documents', 0) + fidelity.get('roundtrip_nonexact_documents', 0) == len(natural)
        documents = examples['documents']
        assert [d['id'] for d in documents] == [r['id'] for r in selected]
        for document, original in zip(documents, selected):
            assert document['text'] == original['text'] and document['collection'] == original['collection']
            assert len(document['token_ids']) == len(document['tokens']) == len(document['decoded_tokens'])
            assert all(isinstance(i, int) and i >= 0 for i in document['token_ids'])
            assert document['roundtrip_exact'] is (document['decoded_text'] == original['text'])
            if document['piece_format'] == 'hex_bytes':
                for piece in document['tokens']:
                    bytes.fromhex(piece)
            if original['category'] == 'characters':
                assert 'SOH-prefix' in document['measurement_context']
    official = [t for t in index['tokenizers'] if t['ranking_eligible']]
    assert len(official) == len(entries)
    assert [t['metrics']['bytes_per_token'] for t in official] == sorted(
        [t['metrics']['bytes_per_token'] for t in official], reverse=True)
    result = {'status': 'complete' if corpus['complete'] else 'partial', 'tokenizers': len(entries),
              'ranked_tokenizers': len(official), 'corpus_documents': len(rows),
              'ranking_documents': len(natural), 'sample_documents': len(selected),
              'corpus_sha256': corpus['sha256'], 'selection_sha256': selection_sha}
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=BASE / 'results')
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    validate(args.output_dir, args.allow_partial)
