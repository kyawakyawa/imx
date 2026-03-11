# imx

`imx` は画像・動画データ処理のための CLI ツールです。複数ディレクトリの画像列を動画化したり、単一チャンネル画像を擬似カラー化したり、重み付き合成や GIF 生成を行えます。

## インストール

前提:

- Python 3.13 以上
- `pip`

リポジトリ直下で以下を実行します。

```bash
pip install -e .
```

インストール後は `imx` コマンドが使えます。

```bash
imx --help
```

## コマンド例

### video

複数ディレクトリの画像列を並べて MP4 を作成します。

```bash
imx video \
  -i data/run_a \
  -i data/run_b \
  -o output.mp4 \
  --sort nat \
  --resize min \
  --title \
  --margin 8
```

主なオプション:

- `--grid 2x2`: グリッドを固定
- `--resize min|max|error`: サイズ不一致時の挙動
- `--codec mp4v|h264`: 出力コーデック
- `--fps 10`: フレームレート

### colorize

単一チャンネル画像をディレクトリ全体の min/max で正規化し、擬似カラー化します。

```bash
imx colorize \
  -i data/grayscale \
  -o data/colorized \
  --cmap VIRIDIS
```

### blend

複数ディレクトリの画像を重み付きで合成します。

```bash
imx blend \
  -i data/run_a \
  -i data/run_b \
  -w 0.7,0.3 \
  -o data/blended \
  --weight-mode normalize
```

主なオプション:

- `--resize min|max|error`
- `--weight-mode normalize|keep`

### gif

画像列から GIF を生成します。

```bash
imx gif \
  -i data/run_a \
  -i data/run_b \
  -o output.gif \
  -d 120 \
  --multi-mode interleave
```

主なオプション:

- `-d, --duration`: 1 フレームあたりの表示時間(ms)
- `--multi-mode concat|interleave`: 複数ディレクトリ時の並べ方

## 補足

- 対象は指定ディレクトリ直下の画像ファイルのみです。再帰探索はしません。
- 複数ディレクトリでファイル数が異なる場合は、最短のディレクトリ長に合わせて処理します。
- 詳細なオプションは `imx <command> --help` で確認できます。
