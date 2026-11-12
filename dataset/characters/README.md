# Character collections

Each JSONL row has `id`, `text`, and `metadata`. `text` contains one Unicode
codepoint. Rows are stored in a fixed order without normalization or deduplication.
`collection_offset` is the zero-based row position within the collection.
Educational kanji are ordered by grade and have a `grade` field.

| File | Documents | Scope |
| --- | ---: | --- |
| `educational_kanji.jsonl` | 1,026 | Six grade lists: 80, 160, 200, 202, 193, 191 |
| `common_kanji.jsonl` | 2,136 | Commonly used kanji |
| `jis_l1.jsonl` | 2,965 | JIS level-1 kanji |
| `jis_l2.jsonl` | 3,618 | JIS level-2-derived collection; includes 228 level-1 characters |

**The level-2-derived collection is not the standard 3,390-character level-2 set.**
An independent check using Python's `euc_jp` codec found all 3,390 level-2
characters and 228 additional level-1 characters. Those additional characters
are exactly the overlap with `jis_l1.jsonl`. All 3,618 characters and their
order are preserved.

[manifest.json](manifest.json) records file hashes, collection counts and the
codec comparison.
