# Third-party notices

The fallback `PAT_STR_B` expression in `GrokAdapter` in
`scripts/evaluate_tokenizers.py` is adapted from the
[SGLang tokenizer implementation](https://github.com/sgl-project/sglang/blob/97a38ee85ba62e268bde6388f1bf8edfe2ca9d76/python/sglang/srt/tokenizer/tiktoken_tokenizer.py).
Only the expression is used; the adapter and artifact loading are implemented
for this benchmark. This adapted portion remains under Apache License 2.0.

Copyright 2023-2024 SGLang Team.

The upstream license is retained in [LICENSES/Apache-2.0-SGLang.txt](LICENSES/Apache-2.0-SGLang.txt).

## Grok 2 result attribution

Powered by xAI.

This product includes materials licensed under the xAI Community License.
All rights reserved. Copyright © xAI 2025.

The [upstream agreement](LICENSES/xai-community.txt), dated November 4, 2025,
is retained for the Grok 2 token-piece/ID result display. The full tokenizer
artifact and model weights are not distributed here. See the
[tokenizer and result conditions](#tokenizerと結果) below for the distinction between numerical measurements, tokenizer-derived content, and
the agreement's output clauses.

## Tokenizerと結果

以下は [固定manifest](dataset/tokenizers.json) のrevisionで確認した配布条件です（2026-11-11確認）。リンク先は各配布元のライセンス原文またはモデルカードです。runnerが取得するtokenizerファイルとモデル重みは、このリポジトリーには同梱していません。

| 結果の識別子 | 配布元とライセンス出典 | 配布条件 |
| --- | --- | --- |
| `plamo3` | [pfnet/plamo-3-610m-fin-instruct](https://huggingface.co/pfnet/plamo-3-610m-fin-instruct/blob/a000b59209f1688322c0804009dc9f3fd67e62c1/README.md) | PLaMo Community License |
| `plamo2` | [pfnet/plamo-2-1b](https://huggingface.co/pfnet/plamo-2-1b/blob/92c75fd6eea9018bcb9c33ee8921589febe071fa/LICENSE) | Apache-2.0 |
| `o200k_harmony` | [openai/tiktoken](https://github.com/openai/tiktoken/blob/4e71bbe0c078468e00fefbf94b39849389f346e5/LICENSE) | MIT |
| `cl100k_base` | [openai/tiktoken](https://github.com/openai/tiktoken/blob/4e71bbe0c078468e00fefbf94b39849389f346e5/LICENSE) | MIT |
| `gemma4` | [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it/blob/4ecc2ba63bcac23ba4a767fc87025b1450f84c9c/README.md) | Apache-2.0 |
| `grok2` | [xai-org/grok-2](https://huggingface.co/xai-org/grok-2/blob/daf4395a80ad177386cfe39641b64fc12b1d70ed/LICENSE) | xAI Community License |
| `cohere-command-a-plus` | [CohereLabs/command-a-plus-05-2026-bf16](https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16/blob/5fb6fde5fd12ff89356aae552e11883bc49f069b/README.md) | Apache-2.0 |
| `mistral-small4` | [mistralai/Mistral-Small-4-119B-2603](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603/blob/a11f36bebf709121056b1dbcc943d1c6afbe494d/README.md) | Apache-2.0 |
| `qwen3_8` | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/LICENSE) | Apache-2.0 |
| `deepseek-v4` | [deepseek-ai/DeepSeek-V4-Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/LICENSE) | MIT |
| `glm5_1` | [zai-org/GLM-5.1](https://huggingface.co/zai-org/GLM-5.1/blob/26e1bd6e011feb778d25ae34b09b07074139d92d/LICENSE) | MIT |
| `llm-jp4` | [llm-jp/llm-jp-4-8b-instruct](https://huggingface.co/llm-jp/llm-jp-4-8b-instruct/blob/098f2b2cf33021eba19a6d3582aa3d071ccc0aff/README.md) | Apache-2.0 |
| `sarashina2_2` | [sbintuitions/sarashina2.2-3b-instruct-v0.1](https://huggingface.co/sbintuitions/sarashina2.2-3b-instruct-v0.1/blob/4f3626fb1b64b3e97c908e67f27b2d627ba2a999/LICENSE) | MIT |

ランキングのtoken数・bytes/token等は入力を符号化した測定値です。`results/` の共通sampleと詳細表示には、元本文、token piece、ID、decodeを含みます。これらを再配布する場合は、数値集計だけを利用する場合と区別し、本文とtokenizerの条件を保持してください。MIT/Apache-2.0の配布物を取得・改変・再配布する場合は、元のライセンス、著作権表示、該当するNOTICEや変更表示を保持する必要があります。

- **PLaMo 3：** `results/pages/plamo3/` と対応する保存結果は、`pfnet/plamo-3-610m-fin-instruct` のtokenizerを使った符号化結果です。Built with PLaMo。[PLaMo Community License](https://plamo.preferredai.jp/info/plamo-community-license-en)（2026-11-09改定）はtokenizerをMODELに含め、encoding等を行うCONVERSION MODELの出力表示には例外を設けています。一方、出力を用いて学習するモデルには同規約が適用され、その旨の告知も求めています。本結果のPLaMo 3出力を学習に用いる場合も、この条件を確認してください。MODEL/DERIVED MODELの再配布には規約の添付・表示等、商用利用には登録・売上条件等があります。
- **Grok 2：** Powered by xAI。token piece・ID表示に関する帰属表示と[規約全文](LICENSES/xai-community.txt)を上記の帰属表示とともに保持しています。[固定版の規約](https://huggingface.co/xai-org/grok-2/blob/daf4395a80ad177386cfe39641b64fc12b1d70ed/LICENSE)の第2節(b)はMaterials・派生物・出力による基盤モデル等の学習を制限し、第4節は出力の利用・改変・共有に制約を課さないと記載しています。両節の関係とtokenizer由来のpiece/IDへの適用範囲は配布元に確認が必要であり、本体MITによる無条件の学習利用許可とは扱いません。Materials等の再配布には規約添付、帰属表示、Powered by xAIの表示が必要です。

## データセット

FineWeb2由来の抜粋は、Hugging Face FineWeb2のデータベースの [ODC-By 1.0](https://opendatacommons.org/licenses/by/1-0/)、[Common Crawlの利用条件](https://commoncrawl.org/terms-of-use)、各原文ページの権利を区別して扱います。本文の出典・revision・採用範囲は各行のmetadata、帰属表示と取得条件は [dataset/README.md](dataset/README.md#fineweb-sources-and-language-scope) に保持しています。原文ページごとの再配布許諾をすべて確認したものではありません。独立執筆文と文字集合についても、来歴は同READMEと [文字集合manifest](dataset/characters/manifest.json) を参照してください。ルートのMITをデータ全体の一括ライセンスとしては適用しません。
