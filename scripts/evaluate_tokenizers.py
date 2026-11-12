#!/usr/bin/env python3
"""Evaluate pinned tokenizer artifacts only; never fetch model weights.

Primary compression metrics exclude singleton character collections. Examples
are a deterministic viewing subset, never the ranking population.
"""
import argparse
import collections
import datetime
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parents[1]
SEED = 20261107


def dump(path, value, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    options = {'separators': (',', ':')} if compact else {'indent': 2}
    temporary.write_text(json.dumps(value, ensure_ascii=False, **options) + '\n')
    temporary.replace(path)


def fetch_artifacts(entry, cache):
    directory = cache / entry['slug'] / entry['revision']
    directory.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for spec in entry['files']:
        name = spec['path'] if isinstance(spec, dict) else spec
        assert not name.startswith('/') and '..' not in Path(name).parts
        assert not any(part in name for part in ('.safetensors', '.bin', 'pytorch_model', 'modeling_'))
        target = directory / name
        url = spec.get('url') if isinstance(spec, dict) else None
        url = url or f'https://huggingface.co/{entry["model_id"]}/resolve/{entry["revision"]}/{name}'
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=120) as response:
                raw = response.read(64_000_001)
            assert len(raw) <= 64_000_000, (name, 'tokenizer file size guard')
            target.write_bytes(raw)
        raw = target.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if isinstance(spec, dict) and spec.get('sha256'):
            assert sha == spec['sha256'], (name, 'artifact hash mismatch')
        artifacts.append({'path': name, 'sha256': sha, 'bytes': len(raw), 'url': url})
    return directory, artifacts


def load_corpus(base=BASE):
    language_manifest = json.loads((base / 'dataset/languages.json').read_text())
    entries = {e['tag']: e for e in language_manifest['languages']}
    rows, files, digest = [], {}, hashlib.sha256()
    for path in sorted((base / 'dataset').glob('*/*.jsonl')):
        relative = str(path.relative_to(base))
        raw = path.read_bytes()
        digest.update(relative.encode() + b'\0' + raw + b'\0')
        documents = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        files[relative] = len(documents)
        for row in documents:
            category, tag = path.parent.name, path.stem
            row = {**row, 'collection': relative, 'category': category}
            row['group'] = (tag if tag in ('en', 'ja') else entries[tag]['tier']) if category == 'fineweb' else category
            row['language'] = tag if category != 'characters' else 'ja'
            rows.append(row)
    missing = [{'language': tag, 'saved': files.get(f'dataset/fineweb/{tag}.jsonl', 0), 'target': 50}
               for tag in entries if files.get(f'dataset/fineweb/{tag}.jsonl', 0) != 50]
    for category in ('news', 'sns', 'code', 'academic'):
        for tag in ('ja', 'en'):
            path = f'dataset/{category}/{tag}.jsonl'
            if files.get(path, 0) != 50:
                missing.append({'collection': path, 'saved': files.get(path, 0), 'target': 50})
    corpus = {'sha256': digest.hexdigest(), 'documents': len(rows), 'complete': not missing,
              'target_documents': 17595, 'incomplete_targets': missing,
              'language_frames': len(entries),
              'excluded_languages': language_manifest.get('scope_update', {}).get('excluded_tags', []),
              'ranking_scope': 'All saved non-character documents; singleton characters excluded.',
              'files': files}
    return rows, corpus


def select_examples(rows):
    by_collection = collections.defaultdict(list)
    for row in rows:
        by_collection[row['collection']].append(row)
    selected = []
    for collection, documents in sorted(by_collection.items()):
        limit = 8 if documents[0]['category'] == 'characters' else 2
        key = lambda r: hashlib.sha256(f'{SEED}\0{r["id"]}'.encode()).digest()
        selected.extend(sorted(documents, key=key)[:limit])
    digest = hashlib.sha256('\n'.join(r['id'] for r in selected).encode()).hexdigest()
    return selected, digest


VOCAB_SIZE_DEFINITION = 'distinct registered token IDs, including added/special tokens; unassigned ID gaps excluded'


def vocabulary_metadata(tokenizer, backend):
    """Count actual registered IDs, not max ID + 1 (which may include gaps)."""
    if backend == 'huggingface':
        ids = set(tokenizer.get_vocab().values())
        method = 'unique IDs in tokenizer.get_vocab()'
    elif backend in ('tiktoken', 'grok-tiktoken'):
        ids = set(tokenizer._mergeable_ranks.values()) | set(tokenizer._special_tokens.values())
        method = 'union of mergeable-rank and special-token IDs'
    else:
        raise ValueError('unsupported vocabulary backend')
    if not ids or any(type(value) is not int or value < 0 for value in ids):
        raise ValueError('invalid registered vocabulary IDs')
    return len(ids), {'definition': VOCAB_SIZE_DEFINITION, 'method': method,
                      'id_capacity': max(ids) + 1}


class HuggingFaceAdapter:
    def __init__(self, entry, cache):
        from transformers import AutoTokenizer
        directory, self.artifacts = fetch_artifacts(entry, cache)
        # Custom tokenizer code is allowed only when explicitly declared audited.
        custom = entry.get('audited_remote_code', False)
        compatibility = {}
        config = json.loads((directory / 'tokenizer_config.json').read_text())
        if isinstance(config.get('extra_special_tokens'), list):
            # New configs use a list here; transformers 4 expects named modality
            # attributes. All token IDs remain in added_tokens_decoder/tokenizer.json.
            compatibility['extra_special_tokens'] = {}
        if config.get('tokenizer_class') == 'TokenizersBackend':
            from transformers import PreTrainedTokenizerFast
            self.tokenizer = PreTrainedTokenizerFast.from_pretrained(str(directory), local_files_only=True,
                                                                    **compatibility)
            compatibility['generic_fast_backend'] = True
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True,
                                                           trust_remote_code=custom, **compatibility)
        self.vocab_size, self.vocab_size_metadata = vocabulary_metadata(self.tokenizer, entry['backend'])
        self.policy = 'encode(add_special_tokens=False); native literal-special recognition; no ID filtering or external normalization'
        if compatibility:
            from tokenizers import Tokenizer
            backend = Tokenizer.from_file(str(directory / 'tokenizer.json'))
            self.reference_backend = backend
            for probe in ('日本語とEnglish 123 test.', '<eos>  \n', 'é e\u0301 👩\u200d🔬'):
                assert self.encode(probe) == backend.encode(probe, add_special_tokens=False).ids
            self.policy += '; transformers4 compatibility adjustments=' + json.dumps(compatibility, sort_keys=True) + '; raw IDs checked against original tokenizer.json for every encoding'

    def encode(self, text):
        ids = self.tokenizer.encode(text, add_special_tokens=False)
        if getattr(self, 'reference_backend', None) is not None:
            assert ids == self.reference_backend.encode(text, add_special_tokens=False).ids, 'Fast-wrapper IDs differ from pinned original tokenizer.json'
        return ids

    def decode(self, ids):
        return self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)

    def pieces(self, ids):
        return self.tokenizer.convert_ids_to_tokens(ids)


class TiktokenAdapter:
    def __init__(self, entry, cache):
        import tiktoken
        from tiktoken.load import load_tiktoken_bpe
        directory, self.artifacts = fetch_artifacts(entry, cache)
        self.tokenizer = tiktoken.get_encoding(entry['encoding'])
        ranks = load_tiktoken_bpe(str(directory / entry['files'][0]['path']))
        assert ranks == self.tokenizer._mergeable_ranks, 'Installed encoding ranks differ from pinned artifact'
        self.vocab_size, self.vocab_size_metadata = vocabulary_metadata(self.tokenizer, entry['backend'])
        self.policy = 'encode_ordinary; literal special-token spellings are ordinary text; no automatic BOS/EOS'

    def encode(self, text):
        return self.tokenizer.encode_ordinary(text)

    def decode(self, ids):
        return self.tokenizer.decode(ids, errors='replace')

    def pieces(self, ids):
        return [self.tokenizer.decode_single_token_bytes(i).hex() for i in ids]


class GrokAdapter(TiktokenAdapter):
    def __init__(self, entry, cache):
        import tiktoken
        directory, self.artifacts = fetch_artifacts(entry, cache)
        source = json.loads((directory / 'tokenizer.tok.json').read_text())
        assert source['word_split'] == 'V1'
        # PAT_STR_B adapted from SGLang (Apache-2.0); see THIRD_PARTY_NOTICES.md.
        # This benchmark supplies its own adapter and artifact-loading code.
        pattern = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
        self.tokenizer = tiktoken.Encoding(name=entry['slug'], pat_str=source.get('pat_str', pattern),
            mergeable_ranks={bytes(x['bytes']): x['token'] for x in source['regular_tokens']},
            special_tokens={bytes(x['bytes']).decode(): x['token'] for x in source['special_tokens']})
        self.vocab_size, self.vocab_size_metadata = vocabulary_metadata(self.tokenizer, entry['backend'])
        self.policy = 'Official Grok rank artifact and SGLang V1 PAT_STR_B; encode_ordinary for raw literal content; no chat framing'


def metric(rows):
    characters = sum(r['characters'] for r in rows)
    utf8_bytes = sum(r['utf8_bytes'] for r in rows)
    tokens = sum(r['tokens'] for r in rows)
    return {'documents': len(rows), 'characters': characters, 'utf8_bytes': utf8_bytes, 'tokens': tokens,
            'chars_per_token': characters / tokens if tokens else None,
            'bytes_per_token': utf8_bytes / tokens if tokens else None}


def evaluate(entry, cache, output, rows, corpus, selected, selection_sha):
    adapters = {'tiktoken': TiktokenAdapter, 'huggingface': HuggingFaceAdapter,
                'grok-tiktoken': GrokAdapter}
    adapter = adapters[entry['backend']](entry, cache)
    records, examples, char_counts = [], [], collections.defaultdict(collections.Counter)
    fidelity = collections.Counter()
    approximate = False  # Only exact-ID tokenizer backends are registered.
    unknown_id = getattr(getattr(adapter, 'tokenizer', None), 'unk_token_id', None)
    selected_ids = {r['id'] for r in selected}
    piece_format = ('marked_approximate_piece' if approximate else
                    'hex_bytes' if entry['backend'] in ('tiktoken', 'grok-tiktoken') else 'native_vocabulary_piece')
    prefix = adapter.encode('\x01')
    for row in rows:
        text = row['text']
        ids = adapter.encode(text)
        character_context = None
        if row['category'] == 'characters':
            prefixed = adapter.encode('\x01' + text)
            length = len(prefixed[len(prefix):])
            character_context = {'prefix': 'U+0001', 'prefix_token_count': len(prefix),
                                 'prefixed_token_count': len(prefixed), 'measured_token_count': length,
                                 'prefix_stable': prefixed[:len(prefix)] == prefix}
            counter = char_counts[row['collection']]
            counter['total'] += 1
            counter['one_token'] += length == 1
            counter['prefix_not_stable'] += prefixed[:len(prefix)] != prefix
        else:
            assert ids, (entry['slug'], row['id'], 'empty tokenization')
            records.append({'id': row['id'], 'collection': row['collection'], 'group': row['group'],
                            'language': row['language'], 'tokens': len(ids), 'characters': len(text),
                            'utf8_bytes': len(text.encode())})
            fidelity['documents'] += 1
            if approximate:
                fidelity['decode_unavailable_documents'] += 1
            else:
                exact = adapter.decode(ids) == text
                fidelity['roundtrip_exact_documents'] += exact
                fidelity['roundtrip_nonexact_documents'] += not exact
                if unknown_id is not None:
                    fidelity['unknown_tokens'] += ids.count(unknown_id)
                    fidelity['documents_with_unknown_tokens'] += unknown_id in ids
        if row['id'] in selected_ids:
            decoded = adapter.decode(ids)
            pieces = adapter.pieces(ids)
            singles = [adapter.decode([token]) for token in ids]
            assert len(ids) == len(pieces) == len(singles)
            examples.append({'id': row['id'], 'collection': row['collection'], 'text': text,
                             'token_ids': [None] * len(ids) if approximate else ids,
                             'tokens': pieces, 'decoded_tokens': singles,
                             'ids_available': not approximate, 'boundaries_approximate': approximate,
                             'piece_format': piece_format,
                             'decoded_text': decoded,
                             'measurement_context': ('Standalone encode(text); character_coverage uses legacy SOH-prefix count stripping, a different context.'
                                                     if row['category'] == 'characters' else None),
                             'character_measurement': character_context,
                             'roundtrip_exact': None if approximate else decoded == text})
    examples_by_id = {r['id']: r for r in examples}
    collections_metrics = {key: metric([r for r in records if r['collection'] == key])
                           for key in sorted({r['collection'] for r in records})}
    groups = {key: metric([r for r in records if r['group'] == key])
              for key in sorted({r['group'] for r in records})}
    coverage = {key: {**value, 'ratio': value['one_token'] / value['total']}
                for key, value in char_counts.items()}
    versions = {'python': platform.python_version()}
    for name in ('transformers', 'tokenizers', 'tiktoken', 'sentencepiece', 'numba', 'protobuf', 'numpy', 'regex'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    summary = {'schema_version': 1, 'tokenizer': entry, 'corpus': corpus, 'metrics': metric(records),
               'collections': collections_metrics, 'groups': groups, 'character_coverage': coverage,
               'vocab_size': adapter.vocab_size,
               'vocab_size_metadata': getattr(adapter, 'vocab_size_metadata', None),
               'encoding_policy': adapter.policy,
               'fidelity': dict(fidelity),
               'ranking_eligible': not approximate,
               'ranking_note': ('Unofficial approximate count reconstruction with no real token IDs or decoder; reference only.' if approximate else 'Pinned executable tokenizer; fidelity indicators reported separately.'),
               'fidelity_note': 'Full non-character document decode equality is a fidelity indicator, not model quality. Native normalization may explain nonexact outputs; no external input normalization was applied.',
               'artifacts': adapter.artifacts, 'package_versions': versions,
               'external_normalization': 'none; original Unicode text and whitespace passed unchanged',
               'backend_normalizer': (json.loads(adapter.tokenizer.backend_tokenizer.to_str()).get('normalizer')
                    if hasattr(getattr(adapter, 'tokenizer', None), 'backend_tokenizer')
                    else 'Native pinned slow/custom tokenizer implementation; artifact hashes retained'),
               'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'character_metric': 'Legacy SOH-prefix token-count stripping; prefix mismatches reported explicitly.',
               'selection_sha256': selection_sha}
    summary['runner_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    directory = output / entry['slug']
    dump(directory / 'summary.json', summary)
    dump(directory / 'examples.json', {'schema_version': 1, 'seed': SEED,
         'selection_sha256': selection_sha, 'corpus_sha256': corpus['sha256'],
         'piece_format': piece_format,
         'tokens_representation': ('Exact token-byte hex; individual UTF-8 decodes may be incomplete and are not aligned source spans.' if piece_format == 'hex_bytes'
             else 'Unofficial normalized marker pieces; approximate boundaries, no real IDs or decoder.' if approximate
             else 'Native vocabulary pieces; individual decodes are not aligned source spans.'),
         'documents': [examples_by_id[r['id']] for r in selected]}, compact=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=BASE / 'dataset/tokenizers.json')
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=BASE / 'results')
    parser.add_argument('--tokenizers', help='Comma-separated slugs; default all manifest entries')
    parser.add_argument('--allow-partial', action='store_true', help='Explicitly label and evaluate an unfinished snapshot')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    entries = manifest['tokenizers']
    if args.tokenizers:
        wanted = set(args.tokenizers.split(','))
        entries = [e for e in entries if e['slug'] in wanted]
        assert {e['slug'] for e in entries} == wanted
    rows, corpus = load_corpus()
    assert corpus['complete'] or args.allow_partial, 'Corpus unfinished; finish it or explicitly pass --allow-partial.'
    selected, selection_sha = select_examples(rows)
    if corpus['complete']:
        assert len(rows) == 17595 and len(selected) == 346
        assert sum(r['category'] != 'characters' for r in rows) == 7850
    for entry in entries:
        print(json.dumps({'event': 'start', 'tokenizer': entry['slug'], 'corpus': corpus['sha256'][:12]}), flush=True)
        result = evaluate(entry, args.cache_dir, args.output_dir, rows, corpus, selected, selection_sha)
        print(json.dumps({'event': 'complete', 'tokenizer': entry['slug'], 'metrics': result['metrics']}), flush=True)
    summaries = []
    for path in sorted(args.output_dir.glob('*/summary.json')):
        summary = json.loads(path.read_text())
        if summary['corpus']['sha256'] != corpus['sha256']:
            continue  # Different snapshots are never ranked together.
        entry = summary['tokenizer']
        if entry['slug'] not in {e['slug'] for e in manifest['tokenizers']}:
            continue  # Removed candidates must not re-enter from old result directories.
        summaries.append({'slug': entry['slug'], 'model_id': entry.get('model_id', entry.get('encoding')),
                          'display_name': entry.get('encoding') or entry['model_id'],
                          'revision': entry.get('revision'), 'vocab_size': summary['vocab_size'],
                          'vocab_size_metadata': summary.get('vocab_size_metadata'),
                          'ranking_eligible': summary['ranking_eligible'], 'ranking_note': summary['ranking_note'],
                          'metrics': summary['metrics'], 'summary_path': f"{entry['slug']}/summary.json",
                          'examples_path': f"{entry['slug']}/examples.json"})
    summaries.sort(key=lambda r: (not r['ranking_eligible'], -r['metrics']['bytes_per_token'], r['slug']))
    dump(args.output_dir / 'index.json', {'schema_version': 1, 'corpus': corpus,
         'ranking_metric': 'bytes_per_token', 'ranking_direction': 'descending',
         'sample_seed': SEED, 'sample_documents': len(selected), 'selection_sha256': selection_sha,
         'tokenizers': summaries})


if __name__ == '__main__':
    main()
