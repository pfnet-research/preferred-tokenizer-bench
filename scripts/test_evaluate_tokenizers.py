import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import evaluate_tokenizers as evaluation


class CharacterAdapter:
    vocab_size = 1000
    artifacts = []
    policy = 'test adapter: exact codepoints, no automatic special tokens'

    def __init__(self, entry, cache):
        pass

    def encode(self, text):
        return [ord(c) for c in text]

    def decode(self, ids):
        return ''.join(chr(i) for i in ids)

    def pieces(self, ids):
        return [f'U+{i:04X}' for i in ids]


class EvaluationTests(unittest.TestCase):
    def test_removed_nondecoding_candidate_is_not_registered(self):
        entries = json.loads((evaluation.BASE / 'dataset/tokenizers.json').read_text())['tokenizers']
        self.assertNotIn('ctok', {entry['backend'] for entry in entries})
        self.assertNotIn('claude-ctok-4_8', {entry['slug'] for entry in entries})
        self.assertFalse(hasattr(evaluation, 'CtokAdapter'))

    def test_single_new_tokenizer_keeps_current_registered_results_only(self):
        entries = [dict(slug=slug, backend='huggingface', model_id=slug, revision='pinned')
                   for slug in ['old', 'new']]
        def summary(entry):
            return dict(tokenizer=entry, corpus=dict(sha256='current'), vocab_size=100,
                        ranking_eligible=True, ranking_note='exact', metrics=dict(bytes_per_token=2.0))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps(dict(tokenizers=entries)))
            for slug in ['old', 'removed']:
                entry = next((e for e in entries if e['slug'] == slug), dict(entries[0], slug=slug))
                evaluation.dump(root / slug / 'summary.json', summary(entry))
            def evaluate(entry, cache, output, *args):
                result = summary(entry)
                evaluation.dump(output / entry['slug'] / 'summary.json', result)
                return result
            arguments = ['evaluate', '--manifest', str(manifest), '--cache-dir', str(root),
                         '--output-dir', str(root), '--tokenizers', 'new', '--allow-partial']
            with patch('sys.argv', arguments), patch.object(evaluation, 'load_corpus', return_value=([], dict(sha256='current', complete=False))), patch.object(evaluation, 'select_examples', return_value=([], 'selection')), patch.object(evaluation, 'evaluate', side_effect=evaluate) as runner:
                evaluation.main()
            self.assertEqual(runner.call_count, 1)
            index = json.loads((root / 'index.json').read_text())
            self.assertEqual({e['slug'] for e in index['tokenizers']}, {'old', 'new'})

    def test_registered_vocabulary_excludes_gaps_includes_specials_and_deduplicates_ids(self):
        hf = SimpleNamespace(get_vocab=lambda: {'normal': 0, 'alias': 0, 'added': 3, '<eos>': 9})
        ranks = SimpleNamespace(_mergeable_ranks={b'a': 0, b'b': 3},
                                _special_tokens={'<eos>': 9, '<alias>': 9})
        for backend, tokenizer in [('huggingface', hf), ('tiktoken', ranks), ('grok-tiktoken', ranks)]:
            size, metadata = evaluation.vocabulary_metadata(tokenizer, backend)
            self.assertEqual(size, 3)
            self.assertEqual(metadata['id_capacity'], 10)
            self.assertEqual(metadata['definition'], evaluation.VOCAB_SIZE_DEFINITION)
        with self.assertRaisesRegex(ValueError, 'vocabulary IDs'):
            evaluation.vocabulary_metadata(SimpleNamespace(get_vocab=lambda: {'a': True}), 'huggingface')

    def test_micro_ratio_uses_totals_not_mean_document_ratios(self):
        result = evaluation.metric([{'characters': 1, 'utf8_bytes': 3, 'tokens': 1},
                                    {'characters': 10, 'utf8_bytes': 10, 'tokens': 10}])
        self.assertAlmostEqual(result['bytes_per_token'], 13 / 11)

    def test_selection_is_stable_under_input_reordering(self):
        rows = [{'id': f'text-{i}', 'collection': 'dataset/fineweb/ja.jsonl',
                 'category': 'fineweb'} for i in range(50)]
        rows += [{'id': f'char-{i}', 'collection': 'dataset/characters/a.jsonl',
                  'category': 'characters'} for i in range(20)]
        chosen, sha = evaluation.select_examples(rows)
        reversed_chosen, reversed_sha = evaluation.select_examples(list(reversed(rows)))
        self.assertEqual(chosen, reversed_chosen)
        self.assertEqual(sha, reversed_sha)
        self.assertEqual(len(chosen), 10)

    def test_characters_excluded_from_primary_and_literal_ids_preserved(self):
        rows = [
            {'id': 'char', 'text': '漢', 'category': 'characters', 'collection': 'chars', 'group': 'characters', 'language': 'ja'},
            {'id': 'doc', 'text': 'A\x01漢', 'category': 'fineweb', 'collection': 'docs', 'group': 'T1', 'language': 'ja'},
        ]
        chosen, sha = evaluation.select_examples(rows)
        with tempfile.TemporaryDirectory() as directory, patch.object(evaluation, 'HuggingFaceAdapter', CharacterAdapter):
            output = Path(directory)
            summary = evaluation.evaluate({'slug': 'test', 'backend': 'huggingface'}, output, output,
                                          rows, {'sha256': 'fixture'}, chosen, sha)
            self.assertEqual(summary['metrics']['documents'], 1)
            self.assertEqual(summary['metrics']['tokens'], 3)
            self.assertEqual(summary['character_coverage']['chars']['ratio'], 1)
            examples = json.loads((output / 'test/examples.json').read_text())['documents']
            example = next(x for x in examples if x['id'] == 'doc')
            self.assertEqual(example['token_ids'], [65, 1, ord('漢')])
            self.assertTrue(example['roundtrip_exact'])


if __name__ == '__main__':
    unittest.main()
