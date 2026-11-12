import copy
import unittest

from review_fineweb import apply_decision
from sample_fineweb import make_candidate


class ReviewDecisionTests(unittest.TestCase):
    def setUp(self):
        entry = {'tag': 'test', 'dataset': 'test-dataset', 'revision': 'test', 'config': 'test_Latn', 'script': 'Latn'}
        source = {'id': 'sample', 'text': 'A synthetic source sentence for testing the span application. ' * 100}
        self.row, private = make_candidate(entry, source, 1, 0, 'https://example.org/api')
        self.proof = {'id': self.row['id'], **private}
        self.decision = {'id': self.row['id'], 'action': 'approve', 'language_confirmed': True,
                         'boundaries_reviewed': True, 'reviewer': 'test-only', 'reviewed_at': 'test-only'}

    def test_explicit_approval_preserves_text_and_source(self):
        approved = apply_decision(self.row, self.proof, self.decision)
        self.assertEqual(approved['text'], self.row['text'])
        self.assertEqual(approved['metadata']['review_status'], 'reviewed')
        self.assertEqual(self.row['metadata']['review_status'], 'pending')
        self.assertEqual(approved['metadata']['source_sha256'], self.row['metadata']['source_sha256'])

    def test_missing_language_confirmation_cannot_export(self):
        del self.decision['language_confirmed']
        with self.assertRaises(AssertionError):
            apply_decision(self.row, self.proof, self.decision)

    def test_span_outside_random_window_is_rejected(self):
        self.decision['source_character_spans'] = [[0, len(self.proof['source']['text'])]]
        with self.assertRaises(AssertionError):
            apply_decision(self.row, self.proof, self.decision)

    def test_changed_source_cannot_reuse_a_decision(self):
        proof = copy.deepcopy(self.proof)
        proof['source']['text'] += 'changed'
        with self.assertRaises(AssertionError):
            apply_decision(self.row, proof, self.decision)

    def test_rejection_does_not_create_a_document(self):
        self.assertIsNone(apply_decision(self.row, self.proof, {'id': self.row['id'], 'action': 'reject'}))


if __name__ == '__main__':
    unittest.main()
