# Dataset files and construction status

The active 149 language frames each contain 50 documents. Together with 400 English/Japanese genre documents and 9,745 character documents, the validated snapshot contains 17,595 documents. `validate_dataset.py --require-complete` passes. The [excerpt audit](construction/review-audit.json) records matching full-source hashes, byte windows and selected spans, along with provenance and reading decisions for all 6,600 excerpts. These checks do not imply native-speaker or factual certification.

All data documents are UTF-8 JSONL objects with exactly these top-level fields:

```json
{"id":"academic-ja-0001","text":"独立して執筆した文章。","metadata":{"source":"original"}}
```

IDs are globally unique. Language tags in file names follow `languages.json`.
Character documents contain one Unicode code point each; prose documents contain
one complete benchmark sample. Original prose has exactly
`{"source":"original"}` as its metadata.

Original samples are independently authored benchmark material, including
invented reporting and synthetic studies; `source: original` does not assert
that their events or findings are true. This provenance belongs in metadata and
dataset-level documentation, not recurring fictional-setting or production/safety
disclaimers in each passage. Such boilerplate distorts the measured vocabulary.
Hypotheses, simulation methods and substantive limitations remain when natural
to the subject. `scripts/audit_original_text.py` highlights representative meta
annotations for contextual review; its candidates are not a banned-word verdict.

- `characters/*.jsonl`: educational/common/JIS character collections. See the
  character manifest for counts, fixed ordering and the level-2-derived scope.
- `{news,sns,code,academic}/{ja,en}.jsonl`: independently written genre samples.
- `fineweb/<language-tag>.jsonl`: **approved outputs only**. T1–T3 use independent
  originals informed by reference style, format and themes; they are not
  translations, paraphrases, or renamed reference passages. T4–T5 use reviewed
  source excerpts with document-level provenance.
- `languages.json`: the current 149 requested evaluation frames: 2 T1, 3 T2,
  12 T3, 36 T4 and 96 active T5. This is 149 frames rather
  than 149 unrelated ISO individual languages: Chinese script frames and
  macrolanguage scopes are explicitly recorded.

An existing partition is not a promise of 50 suitable documents. `coverage.json` records saved rows, while `acquisition-report.json` records the frozen initial acquisition. Candidate counts are distinct from approval counts. The validator's default checks saved rows while reporting missing
frames. `--require-complete` fails unless all requested output targets are met.
An incomplete build must not be reported as a completed 7,450-document corpus.

## FineWeb sources and language scope

[FineWeb2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) is pinned to
`af9c13333eb981300149d5ca60a8e9d659b276b9`. Its dataset card groups data by ISO
639-3 language and ISO 15924 script, and describes the upstream database license
as [ODC-By 1.0](https://opendatacommons.org/licenses/by/1-0/). Attribution to
Hugging Face FineWeb2 is retained here and source dataset/revision, URL, crawl
file path, Common Crawl dump and original document ID accompany each excerpt.
The database license and individual source-page rights are distinct.

FineWeb2 excludes English and explicitly directs users to
[the original FineWeb](https://huggingface.co/datasets/HuggingFaceFW/fineweb).
The English reference source is therefore `HuggingFaceFW/fineweb`, revision
`9bb295ddab0e05d785b879661af7260fed5140fc`, subset `sample-10BT`. It is recorded as
an official fallback, never mislabeled as FineWeb2.

Macro frames are mapped to identified source sublanguages rather than all
related languages pooled together. Examples are `ku` → `kmr_Latn`, `qu` →
`quy_Latn`, `ff` → `fuv_Latn` and `iu` → `ike_Cans` (the former `ik` → `esi_Latn` frame is now excluded).
Their source coverage is narrower than the complete macro. `tl` → `fil_Latn`
is an operational Tagalog/Filipino source match, not an assertion that the two
ISO IDs are identical. `zh-hans` and `zh-hant` share `cmn_Hani`: review must
retain the original matching script; the pipeline does not convert scripts.
The complete mapping and coverage qualifications are in `languages.json`.

## Encoding and approved spans

The `my` baseline retains standard Unicode Myanmar text. Clearly identified
legacy Zawgyi sequences are excluded without conversion, and a mixed source may
contribute only a sufficiently complete standard-Unicode span. The
[Unicode Myanmar FAQ](https://www.unicode.org/faq/myanmar.html) explains the
incompatible character use and ordering; a broad rule alone cannot reliably
identify every ambiguous string. Other legitimate native scripts in the target
language are retained when confirmed during reading.

For approved excerpts, `source_character_spans` is the authoritative source
projection, joined with a single newline between retained spans. The earlier
`excerpt_start_char` and `excerpt_end_char` fields retain the automatic proposal
for traceability; they need not describe the final edited projection.

A previously rejected source may receive a bounded random-window retry using a
new, logged seed. `rewindow_fineweb.py` retains the earlier rejection and proof,
records the originating candidate and attempt, and refuses an original document
already present in the approved output. Repeated windows never count as separate
approved documents; validation enforces original-ID and full-source-hash
uniqueness within each language output.

## Bounded acquisition and review

The sampler uses the Dataset Viewer **rows API**, randomized contiguous blocks
and fixed seed `20261106`; it does not claim uniform sampling over the complete
corpus. The initial frozen acquisition retained eligible rows in block order; later
refills shuffle within the fetched blocks. Neither method is described as a
global uniform document sample. Original
source text must contain at least 2,000 UTF-8 bytes. A reproducible random window
of at least 1,500 bytes is taken on valid character boundaries; the proposed
excerpt is about 1,000 bytes. Source/window/excerpt character and byte offsets,
source hash, seed and API position are retained for reproduction.

The Dataset Viewer API does not bind its row response to a revision parameter.
The dataset main SHA is checked before and after acquisition, and each fetched
source has an individual content hash. API metadata and cached responses are
not distributed; `revision` identifies the repository snapshot checked during
that acquisition, rather than claiming the API itself served a pinned revision.

Language-score and ASCII-mixture flags are review aids. They do not establish
that a passage is in the intended language, and automatic sentence boundaries
are proposals. A reviewer must read each source/window, choose sensible
boundaries, remove other-language material and record explicit decisions before
an excerpt enters `fineweb/`. The pipeline never labels automatic output as
reviewed. Raw full documents, random windows, pending candidates and reading
decisions stay in a private cache outside the committed dataset.

For persistent Viewer failures, a bounded Parquet fallback reads one explicitly chosen
source file, capped at 64 MB. Spanish/Turkish/Cantonese and a Malagasy refill use their small test file after
Viewer read failures; these samples must not be used for model training.
The historically checked Buginese, Navajo, Inupiaq and Cherokee filtered partitions are tiny, with
fewer than 50 eligible original documents. A bounded supplement from the official
older filtered `v2.0.1` revision (`4c6643774aad7f5970955b43fa357008a92471d8`)
adds only distinct original document IDs for Buginese, Inupiaq, Cherokee and
Atikamekw and Meitei. The six audited files total less than 2 MB; no new eligible Navajo
IDs were found. Older filtering can be less precise, so every supplement still requires
linguistic reading. Each row retains its actual older revision. Actual approved
counts are preserved; no foreign-language or duplicated documents are inserted
to reach 50.

```sh
# Standard-library pipeline: private cache must not be committed.
python3 scripts/sample_fineweb.py --cache-dir /absolute/private/cache --workers 1

# Optional bounded fallback; install pyarrow in a local virtual environment.
python3 scripts/sample_fineweb_parquet.py --cache-dir /absolute/private/cache --languages es,tr --split test
python3 scripts/sample_fineweb_parquet.py --cache-dir /absolute/private/cache --languages chr
python3 scripts/supplement_fineweb.py --cache-dir /absolute/private/cache --languages chr --revision 4c6643774aad7f5970955b43fa357008a92471d8

# After reading the actual documents, write explicit decisions and export T4/T5.
python3 scripts/review_fineweb.py --cache-dir /absolute/private/cache --language fa --decisions /absolute/private/fa-decisions.jsonl

python3 scripts/validate_dataset.py
python3 scripts/validate_dataset.py --require-complete
python3 -m unittest discover -s scripts -p 'test_*.py'
```

A review decision is an object containing `id`, `action` (`approve` or `reject`),
`language_confirmed: true`, `boundaries_reviewed: true`, `reviewer`, and
`reviewed_at`. An approval may additionally provide ordered
`source_character_spans: [[start, end], ...]` and notes. These spans refer to the
cached full source and must be contained in its recorded random window. Multiple
spans allow removal of foreign material without pretending the text was a
single contiguous excerpt. Applying a decision records the approved spans and
review identity; it does not itself perform or verify the linguistic reading.

Refilling an existing cache preserves its candidate IDs and source proofs, adding
new IDs after them. Deleting and rebuilding a cache creates a different candidate
pool. Bind reading decisions to the actual source/window inspected, and never
apply decisions from a different candidate snapshot. Acquisition and review
progress remain separate even when the candidate target is extended.

The `bug`, `nv`, `ik`, and `mni` frames were excluded because bounded review yielded only 18, 10, 9, and 48 approved documents respectively, below the 50-document target. Their previous manifest entries and counts remain in [`exclusions.json`](exclusions.json). Active targets are 149 language frames (T5: 96), 7,450 language documents, and 17,595 documents including characters and genres.
