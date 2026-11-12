# AGENTS.md

Working rules for coding agents in preferred-tokenizer-bench.

## Scope and changes

- Read README.md before working. It records the current scope, language
  groups, and the distinction between planned work and implemented behavior.
- Direct commits and pushes to main are allowed for implementation in this
  repository. Pull requests are not required.
  Preserve other contributors' changes and stage only the intended files.
- Do not squash, force-push, or rewrite history.
  This repository-specific workflow does not change workflows in other projects.
- Do not copy legacy datasets, results, vocabulary, or model files without
  checking their provenance, redistribution rights, and confidential content.
  Code, datasets, and models have separate licensing requirements.
- For original benchmark text, disclose authored/synthetic provenance in row
  metadata and dataset-level documentation. Do not insert recurring fictional-
  setting, production-process, or safety disclaimers into individual passages;
  they bias the vocabulary being measured. Keep hypotheses, simulations and
  limitations when they naturally belong to the subject. Review contextual
  audit candidates rather than enforcing a blanket banned-word list.
- Dataset validation and standard-library tests run in CI. Run `python3 -m
  unittest discover -s scripts -p 'test_*.py'` and `python3
  scripts/validate_dataset.py` for applicable changes. Tokenizer evaluation uses
  `scripts/evaluate_tokenizers.py` with optional pinned dependencies; download
  tokenizer artifacts only, never model weights. Report incomplete corpus scopes
  explicitly. Do not cancel or reduce existing CI runs on your own because they
  are slow or expensive.

## Commits and pull requests

- Commit subjects and pull request titles must be in English and follow
  Conventional Commits: `<type>[optional scope][!]: <description>`.
- Commit bodies and pull request descriptions must contain English first,
  followed by a Japanese translation of the same content, including validation
  results. Do not add language headings. Separate the two versions with a
  `-----` line, with a blank line before and after it.
