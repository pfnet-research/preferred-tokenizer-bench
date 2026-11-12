import unittest
from audit_original_text import scan_text


class OriginalTextAuditTests(unittest.TestCase):
    def test_recognizes_origin_labels_and_production_disclaimers(self):
        self.assertTrue(scan_text('[Fiksi]\nA new community garden opens.'))
        self.assertTrue(scan_text('No actual participants were recruited.'))
        self.assertTrue(scan_text('これは架空の調査です。'))

    def test_does_not_ban_technical_subject_vocabulary(self):
        text = 'The simulation tests a hypothesis about particle transport. A limitation is the missing boundary term.'
        self.assertEqual(scan_text(text), [])

    def test_candidates_preserve_context_for_judgment(self):
        text = 'The critic says this story is fictional, then analyzes its narrative voice.'
        self.assertEqual(scan_text(text)[0]['context'], text)


if __name__ == '__main__':
    unittest.main()
