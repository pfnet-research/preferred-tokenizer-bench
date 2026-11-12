# Tokenizerをランキングへ追加する

リポジトリ直下で実行します。登録先は [`dataset/tokenizers.json`](../dataset/tokenizers.json)、評価処理は [`scripts/evaluate_tokenizers.py`](../scripts/evaluate_tokenizers.py) です。モデル重みや推論サーバーは不要です。

## 1. 実装と配布ファイルを固定する

新しいentryをmanifestの `tokenizers` 配列へ追加します。既存entryは残し、`slug` は英数字・`_`・`-`で重複しない名前にします。`model_id`、人向けの `label`、実行方式 `backend`、固定commitの `revision`、一次資料の `source_url` を記録します。tiktokenでは `encoding` も必要です。

現在の結果ページ名は `encoding`、なければ `model_id` から生成されます。`label` だけを変えても表示名は変わりません。独自の表示名を使う変更はindexの `display_name` 生成とテストも対応させてください。

`files` には実行に必要なtokenizer/config/vocabularyだけを列挙し、各 `path`・固定URL・SHA-256・正確なbyte数（`size`）を記録します。tokenizer固有のlicenseと出典を `license` に残し、同じモデルの重みのlicenseや変換済み表示データだけから実行方式を決めないでください。取得した各小ファイルのhashとbyte数は、例えば次の標準ライブラリ処理で確認できます。

```sh
python3 - <<'PYCODE'
import hashlib
from pathlib import Path
p = Path('downloaded-tokenizer-file')
raw = p.read_bytes()
print(p.name, len(raw), hashlib.sha256(raw).hexdigest())
PYCODE
```

以下は**既に登録されているentryを抜粋した例**です。そのまま二重登録せず、新しい対象の実物で値を置き換えます。

### Hugging Face形式

`huggingface` はconfigに従ってAutoTokenizer等を読みます。下記は通常のtokenizer.json/config形式の例です。独自Python tokenizerが必要なPLaMo等は、この2ファイル構成を流用せず実際の依存ファイルを列挙します。

```json
{
  "slug": "gemma4",
  "label": "Gemma 4",
  "backend": "huggingface",
  "model_id": "google/gemma-4-E4B-it",
  "revision": "4ecc2ba63bcac23ba4a767fc87025b1450f84c9c",
  "source_url": "https://github.com/googleapis/python-genai/blob/4bdde3abfde6ec8da1c2c253cb0044991dd6064c/google/genai/_local_tokenizer_loader.py",
  "files": [
    {
      "path": "tokenizer_config.json",
      "size": 3082,
      "sha256": "9f4fec4b1dc6ecddf8f4a92e9caea5971c0e67d81309f3f9066a2bee8c362633",
      "url": "https://huggingface.co/google/gemma-4-E4B-it/resolve/4ecc2ba63bcac23ba4a767fc87025b1450f84c9c/tokenizer_config.json"
    },
    {
      "path": "tokenizer.json",
      "size": 32156428,
      "sha256": "91d9cf86906f78e197021fda88214d448e5c120665d0243a8e776e046986c6bc",
      "url": "https://huggingface.co/google/gemma-4-E4B-it/resolve/4ecc2ba63bcac23ba4a767fc87025b1450f84c9c/tokenizer.json"
    }
  ],
  "license": {
    "id": "apache-2.0",
    "source_url": "https://huggingface.co/google/gemma-4-E4B-it/blob/4ecc2ba63bcac23ba4a767fc87025b1450f84c9c/README.md",
    "terms_url": "https://ai.google.dev/gemma/docs/gemma_4_license"
  }
}
```

### tiktokenのencoding

`tiktoken` は指定encodingを読み、取得したrankファイルとインストール済みencodingのrank一致を確認します。特殊token風の文字列も通常本文として `encode_ordinary` で符号化します。encoding名を未確認の非公開モデル名へ読み替えません。

```json
{
  "slug": "cl100k_base",
  "label": "cl100k_base (OpenAI encoding)",
  "backend": "tiktoken",
  "model_id": "openai/tiktoken",
  "encoding": "cl100k_base",
  "revision": "4e71bbe0c078468e00fefbf94b39849389f346e5",
  "source_url": "https://github.com/openai/tiktoken/blob/4e71bbe0c078468e00fefbf94b39849389f346e5/tiktoken_ext/openai_public.py",
  "implementation_source_url": "https://github.com/openai/tiktoken/blob/4e71bbe0c078468e00fefbf94b39849389f346e5/tiktoken_ext/openai_public.py",
  "files": [
    {
      "path": "cl100k_base.tiktoken",
      "sha256": "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7",
      "size": 1681126,
      "url": "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
    }
  ],
  "license": {
    "id": "MIT",
    "source_url": "https://github.com/openai/tiktoken/blob/4e71bbe0c078468e00fefbf94b39849389f346e5/LICENSE"
  }
}
```

### Grokのrank形式

`grok-tiktoken` は `tokenizer.tok.json` のregular/special ranksとword_split=V1を使います。HFのtokenizer.json形式とは異なります。現在のadapterは公式モデルが参照する固定SGLang実装のPAT_STR_Bを使うため、別形式/別分割規則をこのbackendへ無条件に登録しません。

```json
{
  "slug": "grok2",
  "label": "Grok 2",
  "backend": "grok-tiktoken",
  "model_id": "xai-org/grok-2",
  "revision": "daf4395a80ad177386cfe39641b64fc12b1d70ed",
  "source_url": "https://huggingface.co/xai-org/grok-2/tree/daf4395a80ad177386cfe39641b64fc12b1d70ed",
  "implementation_source_url": "https://github.com/sgl-project/sglang/blob/97a38ee85ba62e268bde6388f1bf8edfe2ca9d76/python/sglang/srt/tokenizer/tiktoken_tokenizer.py",
  "files": [
    {
      "path": "tokenizer.tok.json",
      "url": "https://huggingface.co/xai-org/grok-2/resolve/daf4395a80ad177386cfe39641b64fc12b1d70ed/tokenizer.tok.json",
      "size": 7724637,
      "sha256": "8132d5a6e15d09fdc06680173bb8b30b982f13128c14e14377fbbb77351dcc06"
    }
  ],
  "license": {
    "id": "xai-community",
    "source_url": "https://huggingface.co/xai-org/grok-2/blob/daf4395a80ad177386cfe39641b64fc12b1d70ed/LICENSE"
  }
}
```

必要なcustom tokenizerコードは全文確認し、依存も含めてファイル・revision/hashを固定したうえで `remote_code_files` と `audited_remote_code: true` を記録します。無関係なmodelingコード・重みは追加しません。通常のHF loaderはローカルに取得済みの宣言ファイルだけを読みます。

新しいbackendが必要なら、adapterの `encode(text)`・全列 `decode(ids)`・IDに対応する `pieces(ids)` と語彙数を実装し、dispatchへ追加します。実IDの妥当性、特殊token/BOS/EOSの扱い、空白/改行・結合文字・不完全byteの個別decodeをテストします。IDを推定で補ったり、個別decodeを原文の文字範囲とみなしたりしません。元実装の版と符号化方針、外部正規化を加えない条件も記録します。

語彙数は、追加・特殊トークンを含む異なる登録IDの数で、未割り当てIDは除きます。Hugging Faceでは`get_vocab()`のID集合、tiktokenとGrokでは通常トークンと特殊トークンのID集合の和を数えます。最大IDに1を足した値は、IDの欠番を含むため語彙数の代わりにしません。結果の`vocab_size`に件数、`vocab_size_metadata`に定義・取得方法・ID領域の大きさを保存します。

既存の計測値を変えず、同じ固定版の語彙数だけを確認し直す場合は、次のコマンドを使えます。宣言済みtokenizer資材のSHAを照合し、保存結果と同じ資材であることを確認してからメタデータだけを更新します。モデル重みの取得やコーパスの再評価はしません。

```sh
python3 scripts/update_vocab_sizes.py --cache-dir "$PWD/.cache/tokenizers"
```

## 2. 同じコーパスで評価する

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-tokenizers.txt
python3 scripts/validate_dataset.py --require-complete
python3 scripts/evaluate_tokenizers.py --cache-dir "$PWD/.cache/tokenizers"
```

既定のmanifestと出力先 `results/` を使い、**新entryを含む全registryを評価する**のが標準手順です。キャッシュは `.cache/` にありGit対象外です。認証tokenや秘密値をmanifest、コマンドの記録、commitへ含めません。通常の公開artifact取得にモデル重み/torchは要りません。

同じdataset SHA・共通依存version・登録内容の既存全結果が揃っている場合に限り、`--tokenizers new-slug` で新entryだけ評価できます。runnerは最後に出力先のsummaryを走査し、現manifestに登録済みかつ現在のcorpus SHAが一致する全結果でindexを再構築します。絞り込み対象だけをindexにする仕様ではありません。ただし欠けた既存結果は補完されないため、次のstrict検証で**manifest全件がindexに残ること**を確認します。datasetや共通依存を変えた場合は全registryを再評価してください。

開発用の別manifest/別出力先は `--manifest` / `--output-dir` で指定できますが、最終検証は正本 `dataset/tokenizers.json` と照合します。未完成corpusを許す `--allow-partial` は本番追加の手順には使いません。

## 3. 表示を再生成して検証する

```sh
python3 scripts/generate_reports.py
python3 scripts/validate_dataset.py --require-complete
python3 scripts/validate_results.py
python3 -m unittest discover -s scripts -p 'test_*.py'
git diff --check
```

runnerが同じ固定seedで共通346文書を選び、各tokenizerのsummary/examplesとindexを保存します。全17,595行のうち文章・コード7,850件がoverall順位の対象です。346文書は閲覧専用で、同じID・入力・順序を全tokenizerで共有します。全文decode一致/非一致とUNKを確認し、非一致は正規化仕様も調べて評価条件を説明します。

report生成はREADMEのoverall micro BPT順位、日英各5カテゴリ/T2〜T5の各等重み算術平均BPT順、文字4集合の平均coverage順、モデル別の分割表示ページを更新します。欠測を0で埋めません。生成Markdownを直接編集せず、表と入力/復元表示、詳細へのリンクを確認します。

## 4. mainへ保存する

正本manifest、必要なadapter/tests/依存変更、`results/index.json`、新規・更新されたsummary/examples、生成ページ、READMEを差分確認し、今回分だけ明示的にstageします。既存tokenizerの結果がindexから欠けていないことと、意図しないdataset変更がないことも確認します。tokenizerキャッシュや認証情報はstageしません。

明示stage後は、新規ファイルを含む差分の末尾空白なども確認します。

```sh
git diff --cached --check
```

このrepoはmainへ通常commit/pushする運用です。[AGENTS.md](../AGENTS.md)の英語Conventional subject・英日本文規約に従い、push後にGitHub Actionsの完了と成功を確認します。force pushや履歴書換えは行いません。
