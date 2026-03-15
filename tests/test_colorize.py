from pathlib import Path

import cv2
import numpy as np
from typer.testing import CliRunner

from imx.core.color import build_random_palette, colorize_random_image
from imx.main import app


def test_build_random_palette_keeps_zero_black() -> None:
    unique_values = np.array([0, 1, 2], dtype=np.int64)

    palette = build_random_palette(unique_values, seed=0)

    assert tuple(int(channel) for channel in palette[0]) == (0, 0, 0)
    assert tuple(int(channel) for channel in palette[1]) != (0, 0, 0)
    assert tuple(int(channel) for channel in palette[2]) != (0, 0, 0)


def test_build_random_palette_is_stable_per_value() -> None:
    first = build_random_palette(np.array([1, 3], dtype=np.int64), seed=0)
    second = build_random_palette(np.array([3], dtype=np.int64), seed=0)

    assert tuple(int(channel) for channel in first[1]) == tuple(int(channel) for channel in second[0])


def test_colorize_random_image_applies_force_color(tmp_path: Path) -> None:
    image = np.array([[0, 1], [2, 3]], dtype=np.uint8)
    src = tmp_path / "labels.png"
    assert cv2.imwrite(str(src), image)

    colored = colorize_random_image(src, overrides=[(2, 255, 0, 0)])

    assert tuple(int(channel) for channel in colored[0, 0]) == (0, 0, 0)
    assert tuple(int(channel) for channel in colored[1, 0]) == (0, 0, 255)


def test_colorize_cli_force_color(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    image = np.array([[0, 4], [4, 0]], dtype=np.uint8)
    src = input_dir / "frame.png"
    assert cv2.imwrite(str(src), image)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "colorize",
            "-i",
            str(input_dir),
            "-o",
            str(output_dir),
            "--force-color",
            "4",
            "10",
            "20",
            "30",
        ],
    )

    assert result.exit_code == 0, result.stdout

    saved = cv2.imread(str(output_dir / "frame.png"), cv2.IMREAD_COLOR)
    assert saved is not None
    assert tuple(int(channel) for channel in saved[0, 0]) == (0, 0, 0)
    assert tuple(int(channel) for channel in saved[0, 1]) == (30, 20, 10)
