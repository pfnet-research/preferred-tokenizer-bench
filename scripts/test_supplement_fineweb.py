import copy
import unittest

from sample_fineweb import make_candidate
from supplement_fineweb import append_sources


class SupplementalSourceTests(unittest.TestCase):
    def setUp(self):
        self.current = {'tag': 'test', 'dataset': 'test-dataset', 'revision': 'current',
                        'config': 'test_Latn', 'script': 'Latn'}
        self.older = dict(self.current, revision='older')
        self.source = {'id': 'existing-source', 'text': 'A synthetic existing source sentence. ' * 100}
        self.row, proof = make_candidate(self.current, self.source, 1, 0, 'current-url')
        self.rows = [self.row]
        self.proofs = [{'id': self.row['id'], **proof}]

    def test_duplicate_original_ids_do_not_add_a_second_document(self):
        added = append_sources(self.older, [(0, self.source)], self.rows, self.proofs, 'older-url', 'older.parquet')
        self.assertEqual(added, [])
        self.assertEqual(len(self.rows), 1)

    def test_new_source_preserves_existing_ids_and_records_older_revision(self):
        before = copy.deepcopy(self.rows)
        new = {'id': 'distinct-source', 'text': 'A separate synthetic sentence for the older source. ' * 100}
        added = append_sources(self.older, [(8, new), (9, new)], self.rows, self.proofs, 'older-url', 'older.parquet')
        self.assertEqual(self.rows[:1], before)
        self.assertEqual(added, ['fineweb-test-0002'])
        self.assertEqual(self.rows[-1]['metadata']['revision'], 'older')
        self.assertEqual(self.rows[-1]['metadata']['id'], 'distinct-source')
        self.assertEqual(self.rows[-1]['metadata']['review_status'], 'pending')
        self.assertEqual(self.rows[-1]['metadata']['api_row_index'], 8)
        self.assertEqual(len(self.proofs), 2)


if __name__ == '__main__':
    unittest.main()
