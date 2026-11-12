"""Vocabulary refresh preserves measurements and fails before writing on drift."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import update_vocab_sizes as refresh


class RefreshTests(unittest.TestCase):
    def test_refresh_changes_metadata_only_and_rejects_artifact_drift(self):
        entry = dict(slug='example', backend='huggingface', revision='pinned')
        artifacts = [dict(path='tokenizer.json', sha256='checked')]
        class Adapter:
            def __init__(self, entry, cache):
                self.artifacts = artifacts
                self.vocab_size = 3
                self.vocab_size_metadata = dict(definition='registered IDs', id_capacity=10)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'example').mkdir()
            path = root/'example/summary.json'
            summary = dict(tokenizer=entry, artifacts=artifacts, vocab_size=10,
                           metrics=dict(tokens=123, bytes_per_token=4.5), runner_source_sha256='original')
            index = dict(tokenizers=[dict(slug='example', summary_path='example/summary.json',
                                         vocab_size=10, metrics=summary['metrics'])])
            path.write_text(json.dumps(summary))
            (root/'index.json').write_text(json.dumps(index))
            with patch.object(refresh, 'HuggingFaceAdapter', Adapter):
                refresh.update(dict(tokenizers=[entry]), root, root)
                actual = json.loads(path.read_text())
                self.assertEqual(actual['vocab_size'], 3)
                metadata = actual.pop('vocab_size_metadata')
                actual['vocab_size'] = 10
                self.assertEqual(actual, summary)
                self.assertEqual(json.loads((root/'index.json').read_text())['tokenizers'][0]['vocab_size_metadata'], metadata)
                before = {p: p.read_bytes() for p in (path, root/'index.json')}
                changed = copy.deepcopy(entry) | dict(revision='different')
                with self.assertRaisesRegex(ValueError, 'pinned manifest'):
                    refresh.update(dict(tokenizers=[changed]), root, root)
                self.assertEqual({p: p.read_bytes() for p in before}, before)
                artifacts[0]['sha256'] = 'different'
                with self.assertRaisesRegex(ValueError, 'artifacts differ'):
                    refresh.update(dict(tokenizers=[entry]), root, root)
                self.assertEqual({p: p.read_bytes() for p in before}, before)


if __name__ == '__main__':
    unittest.main()
