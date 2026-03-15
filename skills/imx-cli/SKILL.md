---
name: imx-cli
description: Use this skill when an AI agent needs to run the local imx CLI in this repository for image, video, blend, gif, or colorize workflows. Covers command discovery, fallback execution via imx or uv run imx, and the main subcommand patterns.
---

# imx CLI

この skill は、このリポジトリにある `imx` CLI を AI agent が安全に実行するときに使う。

## 使う場面

- `imx` のサブコマンドで画像処理や動画生成を行うとき
- コマンド例を組み立てるとき
- 実行環境に `imx` コマンドが通っているか不明なとき

## 実行手順

1. まず作業ディレクトリがリポジトリルートか確認する。
2. `imx` がそのまま使えるなら `imx ...` を実行する。
3. `imx` が見つからない場合は `uv run imx ...` を試す。
4. 同じ判定を毎回書かずに済ませたいときは `scripts/run_imx.sh` を使う。

```bash
skills/imx-cli/scripts/run_imx.sh --help
skills/imx-cli/scripts/run_imx.sh video -i data/run_a -o output.mp4
```

## コマンド選択

- `video`: 複数ディレクトリの画像列を並べて動画化
- `colorize`: 単一チャンネル画像のカラー化
- `blend`: 複数ディレクトリの画像の重み付き合成
- `gif`: 画像列から GIF を生成

詳細な例は [references/commands.md](references/commands.md) を読む。

より詳しい使い方や最新の README、実装状況を確認したいときは GitHub リポジトリを参照する:

- <https://github.com/kyawakyawa/imx>

## 注意点

- 対象は指定ディレクトリ直下の画像ファイルのみで、再帰探索しない。
- 複数ディレクトリのファイル数が異なるときは最短系列に揃う。
- サイズ不一致は `--resize min|max|error` で制御する。既定は `error`。
