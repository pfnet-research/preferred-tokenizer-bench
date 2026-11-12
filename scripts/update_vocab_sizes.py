#!/usr/bin/env python3
"""Refresh registered vocabulary sizes from pinned tokenizer-only artifacts.

No corpus evaluation or model weights are needed. Existing measurement source
hashes remain unchanged; vocabulary provenance uses the same manifest/artifacts.
"""
import argparse
import json
from pathlib import Path

from evaluate_tokenizers import (BASE, GrokAdapter, HuggingFaceAdapter,
                                 TiktokenAdapter, dump)


def update(manifest, output, cache):
    entries = {entry['slug']: entry for entry in manifest['tokenizers']}
    index = json.loads((output / 'index.json').read_text())
    if {item['slug'] for item in index['tokenizers']} != set(entries):
        raise ValueError('saved index differs from registered tokenizers')
    pending = []
    adapters = {'huggingface': HuggingFaceAdapter, 'tiktoken': TiktokenAdapter,
                'grok-tiktoken': GrokAdapter}
    for item in index['tokenizers']:
        entry = entries[item['slug']]
        path = output / item['summary_path']
        if path.resolve() != (output / entry['slug'] / 'summary.json').resolve():
            raise ValueError('unexpected summary path')
        summary = json.loads(path.read_text())
        if summary['tokenizer'] != entry:
            raise ValueError('saved result does not use the pinned manifest entry')
        adapter = adapters[entry['backend']](entry, cache)
        if adapter.artifacts != summary['artifacts']:
            raise ValueError('vocabulary artifacts differ from measured artifacts')
        for record in (item, summary):
            record['vocab_size'] = adapter.vocab_size
            record['vocab_size_metadata'] = adapter.vocab_size_metadata
        pending.append((path, summary))
        print(entry['slug'], adapter.vocab_size, flush=True)
    # Fail without modifying saved results if any artifact/loader is unavailable.
    for path, summary in pending:
        dump(path, summary)
    dump(output / 'index.json', index)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=BASE / 'dataset/tokenizers.json')
    parser.add_argument('--output-dir', type=Path, default=BASE / 'results')
    parser.add_argument('--cache-dir', type=Path, required=True)
    args = parser.parse_args()
    update(json.loads(args.manifest.read_text()), args.output_dir, args.cache_dir)
