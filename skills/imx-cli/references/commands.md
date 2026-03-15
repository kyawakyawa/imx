# imx command reference

## ヘルプ確認

```bash
skills/imx-cli/scripts/run_imx.sh --help
skills/imx-cli/scripts/run_imx.sh video --help
skills/imx-cli/scripts/run_imx.sh colorize --help
```

## video

```bash
skills/imx-cli/scripts/run_imx.sh video \
  -i data/run_a \
  -i data/run_b \
  -o output.mp4 \
  --sort nat \
  --resize min \
  --title \
  --margin 8
```

主なオプション:

- `--grid 2x2`
- `--codec mp4v|h264`
- `--fps 10`

## colorize

ランダム色の割り当て:

```bash
skills/imx-cli/scripts/run_imx.sh colorize \
  -i data/grayscale \
  -o data/colorized
```

値ごとの固定色:

```bash
skills/imx-cli/scripts/run_imx.sh colorize \
  -i data/labels \
  -o data/colorized \
  --force-color 1 255 0 0 \
  --force-color 2 0 255 0
```

カラーマップ適用:

```bash
skills/imx-cli/scripts/run_imx.sh colorize \
  -i data/grayscale \
  -o data/colorized \
  --cmap VIRIDIS
```

## blend

```bash
skills/imx-cli/scripts/run_imx.sh blend \
  -i data/run_a \
  -i data/run_b \
  -w 0.7,0.3 \
  -o data/blended \
  --weight-mode normalize
```

## gif

```bash
skills/imx-cli/scripts/run_imx.sh gif \
  -i data/run_a \
  -i data/run_b \
  -o output.gif \
  -d 120 \
  --multi-mode interleave
```
