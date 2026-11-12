"""CPU-only tests of report boundaries, escaping and shared evaluation inputs."""

import copy
import html
import importlib.util
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

spec = importlib.util.spec_from_file_location('generate_reports', Path(__file__).with_name('generate_reports.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'results'
        self.root.mkdir()
        self.readme = self.base / 'README.md'
        self.readme.write_text('# Benchmark\n\nUnchanged instructions.\n')
        self.row = dict(id='doc-1', collection='fineweb/en', text='  hi\t🌏\n\n<script>@name #1 $x$ :smile: https://x.test</script>', token_ids=[0, 7, 8], tokens=['▁hi', '<0xF0>', '<0x9F>'], decoded_tokens=[' hi', '�', '�'], decoded_text=' hi🌏', roundtrip_exact=False)
        self.metrics = dict(characters=100, utf8_bytes=200, tokens=50, chars_per_token=2.0, bytes_per_token=4.0)
        self.index = dict(schema_version=1, corpus=dict(sha256='a'*64, documents=100, target_documents=120, complete=False, excluded_languages=['bug','nv','ik','mni']), tokenizers=[dict(slug='example', model_id='org/example', revision='b'*40, vocab_size=256, summary_path='summary.json', examples_path='examples.json')])
        self.summary = dict(metrics=self.metrics, collections={'fineweb/en': self.metrics}, groups={'en': self.metrics}, character_coverage={'jis_l1': dict(one_token=2000, total=2965, ratio=2000/2965)})
        self.examples = dict(seed=42, selection_sha256='c'*64, documents=[self.row])
        self.save()

    def save(self):
        for name, value in [('index',self.index),('summary',self.summary),('examples',self.examples)]:
            (self.root / (name+'.json')).write_text(json.dumps(value, ensure_ascii=False))

    def test_render_idempotent_and_partitioned(self):
        self.examples['documents'] = [dict(self.row, id=f'doc-{i}') for i in range(23)]
        self.save()
        self.assertEqual(report.generate(self.root, self.readme), (1, 3))
        overview = (self.root/'pages/example/README.md').read_text()
        first = (self.root/'pages/example/part-001.md').read_text()
        second = (self.root/'pages/example/part-002.md').read_text()
        self.assertIn('文書 21–23', overview)
        self.assertEqual(first.count('### 入力'),20)
        self.assertEqual(second.count('### 入力'),3)
        self.assertIn('全列decode一致: **NO**', first)
        self.assertIn('0xF0', html.unescape(re.sub('<[^>]*>', '', first)))
        self.assertNotIn('<script>', first)
        self.assertIn('個別tokenのdecode', first)
        before = self.readme.read_bytes()
        report.generate(self.root, self.readme)
        self.assertEqual(self.readme.read_bytes(), before)
        self.assertTrue(self.readme.read_text().endswith('Unchanged instructions.\n'))

    def test_vocabulary_column_and_missing_value_across_all_rankings(self):
        self.index['tokenizers'][0]['vocab_size'] = 123456
        self.save()
        report.generate(self.root, self.readme)
        text = self.readme.read_text()
        # Overall, two language tables, tiers and character coverage.
        self.assertEqual(text.count('| 語彙数 |'), 5)
        self.assertEqual(text.count('| 123,456 |'), 5)
        self.assertIn('未割り当てIDは除きます', text)
        before = [line.split(' | ')[0] for line in text.splitlines() if 'results/pages/' in line]
        self.index['tokenizers'][0]['vocab_size'] = None
        self.save()
        report.generate(self.root, self.readme)
        text = self.readme.read_text()
        rows = [line for line in text.splitlines() if 'results/pages/' in line]
        self.assertTrue(all('README.md) | — |' in line for line in rows))
        self.assertEqual([line.split(' | ')[0] for line in rows], before)
        self.assertIn('語彙数: —', (self.root/'pages/example/README.md').read_text())
        for invalid in (True, 0, -1, '123', 1.5):
            with self.assertRaisesRegex(ValueError, 'vocabulary size'):
                report.vocabulary_cell({'vocab_size': invalid})

    def test_roundtrip_false_is_not_relabelled(self):
        self.row['roundtrip_exact'] = True
        with self.assertRaisesRegex(ValueError, 'roundtrip flag'):
            report.example(self.row,1)

    def test_unofficial_approximate_backend_never_claims_roundtrip(self):
        row = dict(self.row, ids_available=False, boundaries_approximate=True,
                   token_ids=[None]*3, decoded_tokens=[None]*3,
                   decoded_text=None, roundtrip_exact=None)
        rendered = report.example(row,1)
        self.assertIn('検証不可',rendered)
        self.assertIn('近似境界',rendered)
        self.assertNotIn('一致: **yes**',rendered)
        row['roundtrip_exact'] = False
        with self.assertRaisesRegex(ValueError,'explicitly null'):
            report.example(row,1)

    def test_token_representations_are_not_input_spans(self):
        text = report.example(self.row,1)
        self.assertIn('byte fallback', report.PAGE_NOTES)
        self.assertIn('原文の分割とは限りません',report.PAGE_NOTES)
        self.row['tokens'].pop()
        with self.assertRaisesRegex(ValueError,'different lengths'):
            report.example(self.row,1)

    def test_literal_is_reversible_without_raw_autolinks(self):
        class Text(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []
            def handle_data(self, data):
                self.parts.append(data)
        source = '\\" <tag> &amp; @name :smile: https://example.test $x$\n\t'
        encoded = report.literal(source)
        parser = Text()
        parser.feed(encoded)
        self.assertEqual(json.loads(''.join(parser.parts)),source)
        self.assertNotIn('https://',encoded)

    def test_readable_bytes_and_native_decode_are_explicit(self):
        self.assertEqual(report.readable_piece('48656c6c6f','Hello','hex_bytes'),'Hello')
        self.assertEqual(report.readable_piece('f09f','�','hex_bytes'),'<bytes: F0 9F>')
        self.assertEqual(report.readable_piece('dead',None,'marked_approximate_piece'),'dead')
        self.assertEqual(report.readable_piece('ãĤĴ','あ','native_vocabulary_piece'),'あ')
        self.assertEqual(report.readable_piece('▁hello','hello','native_vocabulary_piece'),'hello')
        self.assertEqual(report.readable_piece('▁','', 'native_vocabulary_piece'),'▁')
        with self.assertRaisesRegex(ValueError,'hex-byte'):
            report.readable_piece('nothex',None,'hex_bytes')

    def test_escape_preserves_codepoints_and_indent(self):
        self.assertEqual(report.quote('  indented\nnext').count('&#160;'),2)
        self.assertIn('\\\n> ',report.quote('a\nb'))
        self.assertFalse(report.quote('last').endswith('\\'))
        self.assertIn('>\n> ',report.quote('a\n\nb'))
        self.assertNotIn('@name',report.escape('@name #1 :smile: https://x.test $x$'))
        self.assertNotIn('a'*40,report.escape('a'*40))
        self.assertIn('🌏',report.escape('🌏'))

    def test_shared_samples_checked_before_writes(self):
        second = dict(self.index['tokenizers'][0], slug='second', examples_path='other.json')
        self.index['tokenizers'].append(second)
        other = copy.deepcopy(self.examples)
        other['documents'][0]['text'] += 'different'
        (self.root/'other.json').write_text(json.dumps(other))
        self.save()
        with self.assertRaisesRegex(ValueError,'same sample'):
            report.generate(self.root,self.readme)
        self.assertFalse((self.root/'pages').exists())

    def test_approximate_backend_is_not_ranked(self):
        tokenizer = dict(self.index['tokenizers'][0], slug='approximate-case', model_id='approximate-case',
                         vocab_size=None, ranking_eligible=False,
                         summary_path='approximate-summary.json', examples_path='approximate-examples.json')
        self.index['tokenizers'].append(tokenizer)
        summary = copy.deepcopy(self.summary)
        summary['metrics'].update(tokens=40, bytes_per_token=5.0, chars_per_token=2.5)
        summary['tokenizer'] = dict(backend='approximate-test', ids_available=False, message_overhead=6)
        summary['fidelity'] = dict(decode_unavailable_documents=100)
        samples = copy.deepcopy(self.examples)
        samples['documents'][0].update(ids_available=False, boundaries_approximate=True,
                                     token_ids=[None]*3, decoded_tokens=[None]*3,
                                     decoded_text=None, roundtrip_exact=None)
        (self.root/'approximate-summary.json').write_text(json.dumps(summary))
        (self.root/'approximate-examples.json').write_text(json.dumps(samples))
        self.save()
        report.generate(self.root,self.readme)
        text = self.readme.read_text()
        self.assertLess(text.index('### 参考値'),text.index('results/pages/approximate-case'))
        overview = (self.root/'pages/approximate-case/README.md').read_text()
        self.assertIn('公式順位の対象外',overview)
        self.assertIn('1検証不可',overview)
        self.assertIn('overhead: 6',overview)

    def test_readme_breakdowns_use_integer_counts_for_every_category(self):
        summary = dict(collections={}, groups={}, character_coverage={})
        expected = []
        for language in ['ja', 'en']:
            for number, genre in enumerate(['fineweb', 'news', 'sns', 'code', 'academic'], 1):
                offset = 0 if language == 'ja' else 20
                values = dict(utf8_bytes=100 + number + offset, tokens=number + 2,
                              bytes_per_token=999.0, chars_per_token=1.0)
                summary['collections'][f'dataset/{genre}/{language}.jsonl'] = values
                expected.append(f"{values['utf8_bytes'] / values['tokens']:.4f}")
        for number, tier in enumerate(['T2', 'T3', 'T4', 'T5'], 1):
            summary['groups'][tier] = dict(utf8_bytes=300 + number, tokens=number + 4,
                                          bytes_per_token=999.0, chars_per_token=1.0)
            expected.append(f'{(300 + number) / (number + 4):.4f}')
        for number, charset in enumerate(['educational_kanji', 'common_kanji', 'jis_l1', 'jis_l2'], 1):
            summary['character_coverage'][f'dataset/characters/{charset}.jsonl'] = dict(
                one_token=number, total=number + 6, ratio=0.99)
            expected.append(f'{number / (number + 6):.2%}')
        rendered = '\n'.join(report.score_breakdowns([(self.index['tokenizers'][0], summary)]))
        for value in expected:
            self.assertIn('| ' + value + ' |', rendered)
        self.assertNotIn('999.0000', rendered)
        self.assertNotIn('99.00%', rendered)
        self.assertIn('第1水準との重複228字', rendered)
        self.summary = summary | dict(metrics=self.metrics)
        self.save()
        report.generate(self.root, self.readme)
        text = self.readme.read_text()
        self.assertIn('[日本語カテゴリ別](#日本語カテゴリ別)', text)
        for heading in ['日本語カテゴリ別', '英語カテゴリ別', '他言語のtier別', '日本語文字集合の単一token率']:
            self.assertIn('### ' + heading, text)
        tables = [line for line in text.splitlines() if line.startswith('| Tokenizer・詳細 |')]
        self.assertEqual([line.count('|') - 1 for line in tables], [8, 8, 7, 7])

    def test_breakdown_missing_counts_are_not_zero_and_invalid_counts_fail(self):
        columns = [('missing', 'groups', 'T5')]
        records = [(self.index['tokenizers'][0], {})]
        text = '\n'.join(report.comparison_table(records, columns))
        self.assertIn('| — |', text)
        self.assertNotIn('0.0000', text)
        records[0][1]['groups'] = dict(T5=dict(utf8_bytes=10))
        self.assertIn('| — | — |', '\n'.join(report.comparison_table(records, columns)))
        records[0][1]['groups'] = dict(T5=dict(utf8_bytes=10, tokens=0))
        with self.assertRaisesRegex(ValueError, 'comparison counts'):
            report.comparison_table(records, columns)
        records[0][1]['groups']['T5'] = dict(one_token=8, total=7)
        with self.assertRaisesRegex(ValueError, 'coverage exceeds'):
            report.comparison_table(records, columns, coverage=True)

    def test_comparison_mean_changes_order_and_missing_is_last(self):
        original = self.index['tokenizers'][0]
        columns = [('a', 'groups', 'a'), ('b', 'groups', 'b')]
        def item(slug, pairs):
            return (dict(original, slug=slug, model_id=slug), {'groups': {
                key: dict(utf8_bytes=top, tokens=bottom) for key, (top, bottom) in pairs.items()}})
        records = [item('overall-first', {'a': (10, 1), 'b': (1, 1)}),
                   item('category-first', {'a': (6, 1), 'b': (6, 1)}),
                   item('missing', {'a': (100, 1)})]
        text = '\n'.join(report.comparison_table(records, columns))
        self.assertLess(text.index('/category-first/'), text.index('/overall-first/'))
        self.assertLess(text.index('/overall-first/'), text.index('/missing/'))
        self.assertIn('| 6.0000 | 6.0000 | 6.0000 |', text)
        self.assertIn('| — | 100.0000 | — |', text)

    def test_mean_uses_unrounded_ratios_and_stable_ties(self):
        original = self.index['tokenizers'][0]
        columns = [('a', 'groups', 'a'), ('b', 'groups', 'b')]
        def item(slug, top):
            return (dict(original, slug=slug, model_id=slug), {'groups': {
                key: dict(utf8_bytes=top, tokens=1000000) for key in ['a', 'b']}})
        records = [item('a-lower', 1000001), item('z-higher', 1000002),
                   item('b-tied', 2000000), item('a-tied', 2000000)]
        text = '\n'.join(report.comparison_table(records, columns))
        self.assertLess(text.index('/z-higher/'), text.index('/a-lower/'))
        self.assertLess(text.index('/a-tied/'), text.index('/b-tied/'))

    def test_coverage_mean_sorts_highest_first(self):
        original = self.index['tokenizers'][0]
        columns = [('a', 'character_coverage', 'a'), ('b', 'character_coverage', 'b')]
        records = [(dict(original, slug=slug, model_id=slug), {'character_coverage': {
            'a': dict(one_token=a, total=10), 'b': dict(one_token=b, total=10)}})
            for slug, a, b in [('low', 10, 0), ('high', 6, 6)]]
        text = '\n'.join(report.comparison_table(records, columns, coverage=True))
        self.assertLess(text.index('/high/'), text.index('/low/'))
        self.assertIn('| 60.00% | 60.00% | 60.00% |', text)

    def test_empty_quote_lines_preserve_paragraph_without_trailing_space(self):
        quoted = report.quote('alpha\n\nbeta')
        self.assertEqual(quoted, '> alpha\n>\n> beta')
        self.assertTrue(all(line == line.rstrip() for line in quoted.splitlines()))

    def test_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError,'within results'):
            report.load_artifact(self.root,'../private.json')
        self.index['tokenizers'][0]['slug']='../private'
        self.save()
        with self.assertRaisesRegex(ValueError,'slug'):
            report.generate(self.root,self.readme)

    def test_limit_and_duplicate_ids_rejected(self):
        self.examples['documents'] *= 2
        self.save()
        with self.assertRaisesRegex(ValueError,'unique shared'):
            report.generate(self.root,self.readme)


if __name__ == '__main__':
    unittest.main()
