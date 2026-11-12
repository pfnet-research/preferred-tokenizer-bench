import unittest
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch
from sample_fineweb import make_candidate, sample_entry


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.entry = {'tag': 'ja', 'dataset': 'HuggingFaceFW/fineweb-2',
                      'revision': 'test-revision', 'config': 'jpn_Jpan', 'script': 'Jpan'}
        self.source = {'id': 'source-1', 'text': (' 前後の文脈を確認するための文章です。段落の境界も確認します。\n' * 100),
                       'url': 'https://example.org/source', 'language': 'jpn', 'language_score': .99}

    def test_utf8_spans_reproduce_exact_source_and_remain_pending(self):
        row, private = make_candidate(self.entry, self.source, 1, 20, 'https://example.org/api')
        meta = row['metadata']
        self.assertGreaterEqual(meta['window_utf8_bytes'], 1500)
        self.assertEqual(self.source['text'][meta['excerpt_start_char']:meta['excerpt_end_char']], row['text'])
        self.assertEqual(self.source['text'][meta['window_start_char']:meta['window_end_char']], private['random_window'])
        self.assertEqual(self.source['text'].encode()[meta['window_start_utf8_byte']:meta['window_end_utf8_byte']].decode(), private['random_window'])
        self.assertEqual(meta['review_status'], 'pending')
        self.assertIn('automatic', meta['boundary_method'])

    def test_reproducible_without_mutating_source(self):
        first = make_candidate(self.entry, self.source, 1, 20, 'url')
        second = make_candidate(self.entry, self.source, 1, 20, 'url')
        self.assertEqual(first, second)
        self.assertEqual(self.source['id'], 'source-1')

    def test_explicit_retry_seed_is_recorded_and_reproducible(self):
        first = make_candidate(self.entry, self.source, 2, 20, 'url', window_seed=123)
        second = make_candidate(self.entry, self.source, 2, 20, 'url', window_seed=123)
        self.assertEqual(first, second)
        self.assertEqual(first[0]['metadata']['sampling_seed'], 123)
        self.assertGreaterEqual(first[0]['metadata']['window_utf8_bytes'], 1500)

    def test_temporary_failed_block_does_not_hide_successful_alternative(self):
        entry = dict(self.entry, train_documents=1000)
        error = urllib.error.HTTPError('https://example.org', 503, 'busy', None, None)
        success = {'rows': [{'row_idx': 20, 'row': self.source, 'truncated_cells': []}], 'partial': False}
        with tempfile.TemporaryDirectory() as temporary, patch('sample_fineweb.fetch_json', side_effect=[error, success]):
            status = sample_entry(entry, Path(temporary), max_pages=2, target=1)
        self.assertEqual(status['candidates'], 1)
        self.assertEqual(status['status'], 'pending_review')
        self.assertIn('HTTP 503', status['errors'][0])

    def test_rejects_short_source(self):
        self.source['text'] = 'あ' * 666
        self.assertIsNone(make_candidate(self.entry, self.source, 1, 0, 'url'))


if __name__ == '__main__':
    unittest.main()
