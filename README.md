# preferred-tokenizer-bench

LLM tokenizerの文字の扱いや文章の分割効率を比較するベンチマークです。
言語ごとの結果と文字集合の被覆を分けて示し、比較条件とデータの来歴を記録しています。

コードと保存結果は [pfnet-research/preferred-tokenizer-bench](https://github.com/pfnet-research/preferred-tokenizer-bench) にあります。

**149言語枠×50件、英日ジャンル文400件、文字集合9,745件の構築・検証を終えました（計17,595件）。文章・コード7,850件を共通入力として13 tokenizerを評価し、各詳細ページで固定346例の分割結果を確認できます。[保存状況](dataset/coverage.json)と[抜粋の確認監査](dataset/construction/review-audit.json)を記録しています。**

データの形式・取得/確認手順・不足の扱いは [`dataset/README.md`](dataset/README.md)、149評価枠のtierとsource対応は [`dataset/languages.json`](dataset/languages.json) を参照してください。

<!-- tokenizer-ranking:start -->
## ランキング

[日本語カテゴリ別](#日本語カテゴリ別) · [英語カテゴリ別](#英語カテゴリ別) · [他言語tier別](#他言語のtier別) · [文字集合率](#日本語文字集合の単一token率)

全コーパスの **Bytes/token（総UTF-8 bytes / 総tokens）降順**。同じ入力集合なら総token数の昇順と一致します。
文字集合の単一token率は別指標です。
データ全体（文字集合を含む） 17,595文書 / 目標 17,595文書 · **complete**。
順位は文字集合を除く7850文書で測定。共通sampleは最大350文書の閲覧用です。
圧縮値は復元の忠実性を保証しません。正規化による非一致もあり、詳細の復元/UNK集計と併せて確認してください。

語彙数は固定版tokenizerに登録された異なるIDの数です。追加・特殊トークンを含み、未割り当てIDは除きます。通常の符号化で特殊トークンを付加するという意味ではありません。未取得は `—` で示し、順位の計算には使いません。



| 順位 | Tokenizer・詳細 | 語彙数 | Tokens ↓ | Chars/token ↑ | Bytes/token ↑ |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | [google&#47;gemma&#45;4&#45;E4B&#45;it](results/pages/gemma4/README.md) | 262,144 | 2,053,725 | 2.7098 | 3.6676 |
| 2 | [o200k&#95;harmony](results/pages/o200k_harmony/README.md) | 201,088 | 2,189,117 | 2.5422 | 3.4407 |
| 3 | [Qwen&#47;Qwen3<span>&#46;</span>8&#45;27B](results/pages/qwen3_8/README.md) | 248,077 | 2,378,241 | 2.3400 | 3.1671 |
| 4 | [CohereLabs&#47;command&#45;a&#45;plus&#45;05&#45;2026&#45;bf16](results/pages/cohere-command-a-plus/README.md) | 255,032 | 2,485,567 | 2.2390 | 3.0304 |
| 5 | [deepseek&#45;ai&#47;DeepSeek&#45;V4&#45;Pro](results/pages/deepseek-v4/README.md) | 129,280 | 2,567,849 | 2.1672 | 2.9333 |
| 6 | [mistralai&#47;Mistral&#45;Small&#45;4&#45;119B&#45;2603](results/pages/mistral-small4/README.md) | 131,072 | 2,634,008 | 2.1128 | 2.8596 |
| 7 | [zai&#45;org&#47;GLM&#45;5<span>&#46;</span>1](results/pages/glm5_1/README.md) | 154,856 | 2,836,136 | 1.9622 | 2.6558 |
| 8 | [xai&#45;org&#47;grok&#45;2](results/pages/grok2/README.md) | 131,072 | 2,919,106 | 1.9064 | 2.5803 |
| 9 | [llm&#45;jp&#47;llm&#45;jp&#45;4&#45;8b&#45;instruct](results/pages/llm-jp4/README.md) | 196,608 | 3,013,270 | 1.8469 | 2.4997 |
| 10 | [cl100k&#95;base](results/pages/cl100k_base/README.md) | 100,261 | 3,244,038 | 1.7155 | 2.3218 |
| 11 | [pfnet&#47;plamo&#45;3&#45;610m&#45;fin&#45;instruct](results/pages/plamo3/README.md) | 107,520 | 3,344,648 | 1.6639 | 2.2520 |
| 12 | [pfnet&#47;plamo&#45;2&#45;1b](results/pages/plamo2/README.md) | 100,000 | 3,566,524 | 1.5604 | 2.1119 |
| 13 | [sbintuitions&#47;sarashina2<span>&#46;</span>2&#45;3b&#45;instruct&#45;v0<span>&#46;</span>1](results/pages/sarashina2_2/README.md) | 102,400 | 3,856,086 | 1.4432 | 1.9533 |

文章の各カテゴリ・tier列は総UTF-8 bytes / 総tokensの **Bytes/token ↑**。各表の平均列は列の単純算術平均（高いほど良い）で、表ごとに個別に並べます。カテゴリ・tier・文字集合はそれぞれ同じ重みで、全体のmicro比率とは異なります。平均は丸め前の整数比から計算し、同率はslug順です。欠測は `—` として平均未定・末尾に置き、0とは扱いません。

### 日本語カテゴリ別

各カテゴリ50文書、計250文書（完全なコーパスの場合）。一般文は言語別の独立原稿です。

**正式tokenizer**

| Tokenizer・詳細 | 語彙数 | 平均 ↑ | 一般文 | News | SNS | Code | Academic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [pfnet&#47;plamo&#45;3&#45;610m&#45;fin&#45;instruct](results/pages/plamo3/README.md) | 107,520 | 5.8779 | 7.0753 | 6.2039 | 6.7011 | 3.3959 | 6.0132 |
| [pfnet&#47;plamo&#45;2&#45;1b](results/pages/plamo2/README.md) | 100,000 | 5.8369 | 6.9580 | 6.1403 | 6.6470 | 3.5224 | 5.9167 |
| [llm&#45;jp&#47;llm&#45;jp&#45;4&#45;8b&#45;instruct](results/pages/llm-jp4/README.md) | 196,608 | 5.7556 | 6.8523 | 6.0299 | 6.4228 | 3.3131 | 6.1597 |
| [sbintuitions&#47;sarashina2<span>&#46;</span>2&#45;3b&#45;instruct&#45;v0<span>&#46;</span>1](results/pages/sarashina2_2/README.md) | 102,400 | 5.7145 | 6.8764 | 6.0541 | 6.4202 | 3.1754 | 6.0461 |
| [CohereLabs&#47;command&#45;a&#45;plus&#45;05&#45;2026&#45;bf16](results/pages/cohere-command-a-plus/README.md) | 255,032 | 4.9360 | 5.5504 | 4.9560 | 5.3639 | 3.8307 | 4.9790 |
| [Qwen&#47;Qwen3<span>&#46;</span>8&#45;27B](results/pages/qwen3_8/README.md) | 248,077 | 4.7816 | 5.3769 | 4.8628 | 5.2158 | 3.5360 | 4.9164 |
| [google&#47;gemma&#45;4&#45;E4B&#45;it](results/pages/gemma4/README.md) | 262,144 | 4.6024 | 5.1414 | 4.6120 | 5.0477 | 3.3555 | 4.8554 |
| [deepseek&#45;ai&#47;DeepSeek&#45;V4&#45;Pro](results/pages/deepseek-v4/README.md) | 129,280 | 4.0597 | 4.3131 | 4.0450 | 4.2369 | 3.5117 | 4.1919 |
| [xai&#45;org&#47;grok&#45;2](results/pages/grok2/README.md) | 131,072 | 3.8964 | 4.1041 | 3.8652 | 4.0433 | 3.5487 | 3.9207 |
| [zai&#45;org&#47;GLM&#45;5<span>&#46;</span>1](results/pages/glm5_1/README.md) | 154,856 | 3.8680 | 4.0882 | 3.8071 | 4.0806 | 3.5406 | 3.8237 |
| [o200k&#95;harmony](results/pages/o200k_harmony/README.md) | 201,088 | 3.5920 | 3.6818 | 3.5116 | 3.7466 | 3.5044 | 3.5156 |
| [mistralai&#47;Mistral&#45;Small&#45;4&#45;119B&#45;2603](results/pages/mistral-small4/README.md) | 131,072 | 3.5707 | 3.8246 | 3.4576 | 3.8115 | 3.3603 | 3.3994 |
| [cl100k&#95;base](results/pages/cl100k_base/README.md) | 100,261 | 2.7347 | 2.7100 | 2.5253 | 2.7532 | 3.1633 | 2.5218 |

### 英語カテゴリ別

各カテゴリ50文書、計250文書（完全なコーパスの場合）。一般文は言語別の独立原稿です。

**正式tokenizer**

| Tokenizer・詳細 | 語彙数 | 平均 ↑ | 一般文 | News | SNS | Code | Academic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [pfnet&#47;plamo&#45;2&#45;1b](results/pages/plamo2/README.md) | 100,000 | 5.9151 | 6.7097 | 6.4682 | 6.0838 | 3.5826 | 6.7313 |
| [pfnet&#47;plamo&#45;3&#45;610m&#45;fin&#45;instruct](results/pages/plamo3/README.md) | 107,520 | 5.7394 | 6.5434 | 6.2339 | 5.8310 | 3.4285 | 6.6602 |
| [CohereLabs&#47;command&#45;a&#45;plus&#45;05&#45;2026&#45;bf16](results/pages/cohere-command-a-plus/README.md) | 255,032 | 5.2786 | 5.4598 | 5.6377 | 5.2300 | 3.9783 | 6.0874 |
| [o200k&#95;harmony](results/pages/o200k_harmony/README.md) | 201,088 | 5.2196 | 5.4232 | 5.5856 | 5.1983 | 3.9206 | 5.9703 |
| [xai&#45;org&#47;grok&#45;2](results/pages/grok2/README.md) | 131,072 | 5.2131 | 5.4348 | 5.5946 | 5.1217 | 3.8818 | 6.0324 |
| [zai&#45;org&#47;GLM&#45;5<span>&#46;</span>1](results/pages/glm5_1/README.md) | 154,856 | 5.1791 | 5.4045 | 5.5475 | 5.0859 | 3.9240 | 5.9334 |
| [cl100k&#95;base](results/pages/cl100k_base/README.md) | 100,261 | 5.1791 | 5.4039 | 5.5469 | 5.0859 | 3.9252 | 5.9334 |
| [deepseek&#45;ai&#47;DeepSeek&#45;V4&#45;Pro](results/pages/deepseek-v4/README.md) | 129,280 | 5.1536 | 5.4039 | 5.5380 | 5.0789 | 3.7881 | 5.9591 |
| [mistralai&#47;Mistral&#45;Small&#45;4&#45;119B&#45;2603](results/pages/mistral-small4/README.md) | 131,072 | 5.0990 | 5.3286 | 5.4681 | 5.0095 | 3.7767 | 5.9119 |
| [Qwen&#47;Qwen3<span>&#46;</span>8&#45;27B](results/pages/qwen3_8/README.md) | 248,077 | 5.0706 | 5.3722 | 5.4367 | 4.9496 | 3.6571 | 5.9374 |
| [google&#47;gemma&#45;4&#45;E4B&#45;it](results/pages/gemma4/README.md) | 262,144 | 5.0447 | 5.3919 | 5.4670 | 4.8926 | 3.4596 | 6.0127 |
| [llm&#45;jp&#47;llm&#45;jp&#45;4&#45;8b&#45;instruct](results/pages/llm-jp4/README.md) | 196,608 | 4.9154 | 5.3574 | 5.2644 | 4.7273 | 3.2841 | 5.9438 |
| [sbintuitions&#47;sarashina2<span>&#46;</span>2&#45;3b&#45;instruct&#45;v0<span>&#46;</span>1](results/pages/sarashina2_2/README.md) | 102,400 | 4.1646 | 4.5541 | 4.4513 | 4.1341 | 3.0342 | 4.6491 |

### 他言語のtier別

英語・日本語を除く147言語枠、計7,350文書（完全なコーパスの場合）。tier内の総数から求めるmicro比率です。

**正式tokenizer**

| Tokenizer・詳細 | 語彙数 | 平均 ↑ | T2 | T3 | T4 | T5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [google&#47;gemma&#45;4&#45;E4B&#45;it](results/pages/gemma4/README.md) | 262,144 | 4.2978 | 4.4207 | 5.0325 | 4.5039 | 3.2342 |
| [Qwen&#47;Qwen3<span>&#46;</span>8&#45;27B](results/pages/qwen3_8/README.md) | 248,077 | 4.1662 | 4.9736 | 5.1955 | 3.7628 | 2.7330 |
| [o200k&#95;harmony](results/pages/o200k_harmony/README.md) | 201,088 | 4.0941 | 3.8305 | 4.9037 | 4.6841 | 2.9580 |
| [CohereLabs&#47;command&#45;a&#45;plus&#45;05&#45;2026&#45;bf16](results/pages/cohere-command-a-plus/README.md) | 255,032 | 3.8757 | 4.6440 | 4.9412 | 3.2283 | 2.6893 |
| [deepseek&#45;ai&#47;DeepSeek&#45;V4&#45;Pro](results/pages/deepseek-v4/README.md) | 129,280 | 3.5915 | 4.3172 | 4.1367 | 3.3130 | 2.5991 |
| [mistralai&#47;Mistral&#45;Small&#45;4&#45;119B&#45;2603](results/pages/mistral-small4/README.md) | 131,072 | 3.5357 | 3.5844 | 4.6142 | 3.4720 | 2.4722 |
| [zai&#45;org&#47;GLM&#45;5<span>&#46;</span>1](results/pages/glm5_1/README.md) | 154,856 | 3.1815 | 3.6809 | 4.0456 | 2.5349 | 2.4647 |
| [xai&#45;org&#47;grok&#45;2](results/pages/grok2/README.md) | 131,072 | 3.1176 | 3.9934 | 3.5929 | 2.4919 | 2.3921 |
| [llm&#45;jp&#47;llm&#45;jp&#45;4&#45;8b&#45;instruct](results/pages/llm-jp4/README.md) | 196,608 | 3.0875 | 4.9901 | 2.5787 | 2.4254 | 2.3559 |
| [pfnet&#47;plamo&#45;3&#45;610m&#45;fin&#45;instruct](results/pages/plamo3/README.md) | 107,520 | 2.6209 | 3.1494 | 3.2355 | 1.9640 | 2.1346 |
| [cl100k&#95;base](results/pages/cl100k_base/README.md) | 100,261 | 2.5144 | 2.4049 | 3.2852 | 2.1462 | 2.2212 |
| [pfnet&#47;plamo&#45;2&#45;1b](results/pages/plamo2/README.md) | 100,000 | 2.4628 | 3.1017 | 2.9814 | 1.7017 | 2.0664 |
| [sbintuitions&#47;sarashina2<span>&#46;</span>2&#45;3b&#45;instruct&#45;v0<span>&#46;</span>1](results/pages/sarashina2_2/README.md) | 102,400 | 2.0161 | 2.0680 | 2.4454 | 1.6168 | 1.9343 |

### 日本語文字集合の単一token率

**単一token率 ↑**（単一tokenで表せる文字数 / 集合の文字数）。文章のBytes/tokenとは独立した指標で、総合順位には混ぜません。測定はSOH-prefix条件です。JIS第2水準由来集合は旧集合3,618字を保持しており、第1水準との重複228字を含みます。

**正式tokenizer**

| Tokenizer・詳細 | 語彙数 | 平均 ↑ | 教育漢字 | 常用漢字 | JIS第1水準 | JIS第2水準由来 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [llm&#45;jp&#47;llm&#45;jp&#45;4&#45;8b&#45;instruct](results/pages/llm-jp4/README.md) | 196,608 | 97.59% | 100.00% | 100.00% | 99.93% | 90.44% |
| [google&#47;gemma&#45;4&#45;E4B&#45;it](results/pages/gemma4/README.md) | 262,144 | 92.86% | 100.00% | 99.91% | 98.89% | 72.64% |
| [pfnet&#47;plamo&#45;3&#45;610m&#45;fin&#45;instruct](results/pages/plamo3/README.md) | 107,520 | 86.58% | 100.00% | 99.91% | 99.19% | 47.24% |
| [pfnet&#47;plamo&#45;2&#45;1b](results/pages/plamo2/README.md) | 100,000 | 82.56% | 100.00% | 99.53% | 98.15% | 32.56% |
| [Qwen&#47;Qwen3<span>&#46;</span>8&#45;27B](results/pages/qwen3_8/README.md) | 248,077 | 80.51% | 99.90% | 97.47% | 88.16% | 36.48% |
| [deepseek&#45;ai&#47;DeepSeek&#45;V4&#45;Pro](results/pages/deepseek-v4/README.md) | 129,280 | 76.06% | 97.37% | 88.95% | 80.51% | 37.42% |
| [sbintuitions&#47;sarashina2<span>&#46;</span>2&#45;3b&#45;instruct&#45;v0<span>&#46;</span>1](results/pages/sarashina2_2/README.md) | 102,400 | 71.58% | 99.90% | 96.25% | 81.55% | 8.62% |
| [CohereLabs&#47;command&#45;a&#45;plus&#45;05&#45;2026&#45;bf16](results/pages/cohere-command-a-plus/README.md) | 255,032 | 71.24% | 99.42% | 91.15% | 75.75% | 18.66% |
| [zai&#45;org&#47;GLM&#45;5<span>&#46;</span>1](results/pages/glm5_1/README.md) | 154,856 | 63.82% | 87.23% | 75.28% | 67.18% | 25.59% |
| [xai&#45;org&#47;grok&#45;2](results/pages/grok2/README.md) | 131,072 | 61.89% | 95.13% | 76.73% | 62.33% | 13.38% |
| [o200k&#95;harmony](results/pages/o200k_harmony/README.md) | 201,088 | 55.08% | 89.47% | 66.48% | 53.52% | 10.86% |
| [mistralai&#47;Mistral&#45;Small&#45;4&#45;119B&#45;2603](results/pages/mistral-small4/README.md) | 131,072 | 43.04% | 78.17% | 49.49% | 38.25% | 6.27% |
| [cl100k&#95;base](results/pages/cl100k_base/README.md) | 100,261 | 15.79% | 32.16% | 17.04% | 12.65% | 1.33% |
<!-- tokenizer-ranking:end -->

## 測るもの

- 文章：token数、Unicodeコードポイント数、UTF-8 bytes、chars/token、bytes/token。
- 文字集合：JIS等の指定集合を単一tokenで表現できる割合と分割数。
- 比較条件：tokenizerのrevision、特殊token・正規化・空白・改行の扱いを記録します。

文字集合は自然文と別枠で集計します。異なる文字体系のchars/tokenを、そのまま能力の優劣を示す値としては扱いません。
総合順位は、文字集合を除く全文書の総UTF-8 bytes / 総tokens（micro、降順）で比較します。言語・tier・英日ジャンルの内訳も各集合の総数から求めたmicro比率です。この指標はLLMの回答品質を示しません。

## 言語グループ

言語と文字体系を149の評価枠に分け、T1〜T5をこのベンチマークの集計区分として使います。英語と日本語はT1に属し、結果ではそれぞれ独立して表示します。

| 評価グループ | 言語コードと名前 |
| --- | --- |
| 英語 | `en` 英語 |
| 日本語 | `ja` 日本語 |
| T2 | `zh-hans` 中国語・簡体字、`zh-hant` 中国語・繁体字、`ko` 韓国語 |
| T3 | `ar` アラビア語、`de` ドイツ語、`es` スペイン語、`fr` フランス語、`hu` ハンガリー語、`id` インドネシア語、`it` イタリア語、`nl` オランダ語、`pl` ポーランド語、`ru` ロシア語、`th` タイ語、`vi` ベトナム語 |
| T4 | `hi` ヒンディー語、`fa` ペルシア語、`bn` ベンガル語、`tl` タガログ語、`he` ヘブライ語、`ta` タミル語、`my` ビルマ語、`ur` ウルドゥー語、`ms` マレー語、`ne` ネパール語、`ca` カタルーニャ語、`ml` マラヤーラム語、`bg` ブルガリア語、`sr` セルビア語、`hr` クロアチア語、`sk` スロバキア語、`sl` スロベニア語、`si` シンハラ語、`az` アゼルバイジャン語、`ka` ジョージア語、`hy` アルメニア語、`uz` ウズベク語、`lt` リトアニア語、`km` クメール語、`lv` ラトビア語、`et` エストニア語、`eu` バスク語、`ceb` セブアノ語、`be` ベラルーシ語、`te` テルグ語、`jv` ジャワ語、`kk` カザフ語、`mr` マラーティー語、`sw` スワヒリ語、`gu` グジャラート語、`pa` パンジャーブ語 |
| T5 | 上位tierと重複しない96評価枠。全リストは [`dataset/languages.json`](dataset/languages.json) のT5を参照。マクロ言語は1枠として集計 |

各評価枠の保存状況は[coverage](dataset/coverage.json)、評価条件は各tokenizerの詳細ページで確認できます。

T5は、知名度・有用性と地域・系統・文字・綴りの追加価値、近接言語との重複を考慮して選定しました。Wikipediaの言語版と規模を選定の参考にし、評価にはFineWeb2由来の抜粋を使っています。マクロ言語や中国語諸変種の対象範囲、FineWeb2の各partitionとの対応は [`dataset/languages.json`](dataset/languages.json) に記録しています。

当初の100枠から、50件に満たなかった `bug` / `nv` / `ik` / `mni` の4枠を除外し、現在のT5は96枠、全体は149枠です。以前の対象と保存件数は[除外記録](dataset/exclusions.json)に残しています。

## データの来歴

データは、既存文字集合、独立して執筆した文章、FineWeb2由来の抜粋で構成しています。

文字集合の件数、データのhash、JIS区分との照合結果は [`dataset/characters/manifest.json`](dataset/characters/manifest.json) に記録しています。
JIS第2水準由来集合は、標準の3,390字と第1水準の228字を合わせた3,618字の集合です。

英日ジャンル文とT1〜T3の一般文は、このベンチマーク向けに独立して執筆した文章です。架空の出来事や研究を扱う文章も含みます。各行のmetadataは `{"source":"original"}` です。

T4〜T5はFineWeb2由来の読取確認済み抜粋です。出典URL、データセットのrevision、ライセンス表記、原文hash、採用した文字範囲、確認記録を各行のmetadataに保持しています。

## 結果の表示

詳細レポートには言語・カテゴリ別の集計、tokenごとの表示、実ID、個別decodeと全列decodeを掲載しています。数値と共通sampleは詳細ページからJSONで取得できます。

## 実行と結果

標準ライブラリの構築・レポート検証は次のコマンドで実行します。GitHub Actionsでも、テスト・保存行・結果の整合を検証します。

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_dataset.py
python3 scripts/validate_dataset.py --require-complete
```

tokenizer評価は、専用の仮想環境に `requirements-tokenizers.txt` を導入し、公開artifactの[固定manifest](dataset/tokenizers.json)からtokenizerファイルだけを取得して実行します。モデル重みや推論モデルは取得しません。

```sh
python3 scripts/evaluate_tokenizers.py --cache-dir /absolute/private/tokenizer-cache
python3 scripts/generate_reports.py
python3 scripts/validate_results.py
```

runnerは未完成データを既定で拒否します。明示的な `--allow-partial` は開発中の別出力先用で、部分結果にはPARTIALとdataset hashを記録します。異なるdataset hashの結果を同じランキングに混ぜません。
文字集合9,745件は圧縮順位から除き、SOH-prefix条件による1token率を別集計します。閲覧用は全149枠×2件、英日8ジャンル×2件、4文字集合×8件の共通346件（固定seed）で、順位はこのサンプルではなく全文書から計算します。token piece、実ID、個別decodeは元文字の位置と必ずしも一致しません。全列decodeの一致・不一致とUNK件数を別途記録します。

現行13 tokenizerの計測値は、同一の確定コーパスで得た保存結果です。各summaryの `runner_source_sha256` は、実際に計測した評価スクリプトの版のhashを記録しています。

配布データはmetadataのみを改訂し、再評価は行っていません。本文・ID・順序は計測時と同一です。[計測時と配布版のhash対応・同一性の記録](results/corpus-metadata-revision.json)を掲載しています。

通常の符号化は `add_special_tokens=False`、tiktokenは `encode_ordinary` を使い、入力に含まれる特殊tokenと同じIDを無差別に除きません。外部のUnicode正規化は行わず、backend内部の正規化とpackage versionを結果へ記録します。

## 新しいtokenizerを追加する

[登録・同一コーパスでの評価・ランキング更新手順](docs/adding-tokenizer.md)を参照してください。固定revisionとtokenizerファイルのhashを登録し、既存結果を保持して共通346例とREADMEの各表を再生成する流れをまとめています。

## ライセンス

### このリポジトリーのライセンス

独自に実装したコードと文書は [MIT License](LICENSE) で提供します。

### 他のライセンス一覧

今回の評価に使用した配布物とコードのライセンスです。

| 対象 | ライセンス |
| --- | --- |
| OpenAI、DeepSeek、GLM、Sarashinaのtokenizer | MIT |
| PLaMo 2、Gemma 4、Command A+、Mistral Small 4、Qwen、LLM-jpのtokenizerとSGLang由来コード | Apache-2.0 |
| PLaMo 3のtokenizer | PLaMo Community License (Built with PLaMo) |
| Grok 2のtokenizer | xAI Community License (Powered by xAI) |
| FineWeb2のデータベース | ODC-By 1.0 |

結果やデータの再利用には、元本文と各tokenizerの条件も適用されます。[各配布元のライセンス・帰属表示・利用条件](THIRD_PARTY_NOTICES.md)を参照してください。
