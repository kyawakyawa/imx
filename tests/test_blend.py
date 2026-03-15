from pathlib import Path

import cv2
import numpy as np
import pytest
from typer.testing import CliRunner

from imx.core.blend import blend_images, parse_black_transparent_flags
from imx.main import app


def test_parse_black_transparent_flags_defaults_to_false() -> None:
    assert parse_black_transparent_flags(None, 3) == [False, False, False]


def test_parse_black_transparent_flags_accepts_truthy_and_falsy_values() -> None:
    assert parse_black_transparent_flags("true,0,yes", 3) == [True, False, True]


def test_parse_black_transparent_flags_rejects_wrong_count() -> None:
    with pytest.raises(ValueError, match="must match number of input directories"):
        parse_black_transparent_flags("true,false", 3)


def test_blend_images_treats_black_as_transparent_per_input() -> None:
    black = np.zeros((1, 1, 3), dtype=np.uint8)
    blue = np.array([[[255, 0, 0]]], dtype=np.uint8)

    blended = blend_images([black, blue], [0.5, 0.5], "error", [True, False])

    assert tuple(int(channel) for channel in blended[0, 0]) == (255, 0, 0)


def test_blend_images_keeps_black_without_transparency_flag() -> None:
    black = np.zeros((1, 1, 3), dtype=np.uint8)
    blue = np.array([[[255, 0, 0]]], dtype=np.uint8)

    blended = blend_images([black, blue], [0.5, 0.5], "error", [False, False])

    assert tuple(int(channel) for channel in blended[0, 0]) == (127, 0, 0)


def test_blend_cli_supports_black_transparent(tmp_path: Path) -> None:
    input_a = tmp_path / "a"
    input_b = tmp_path / "b"
    output_dir = tmp_path / "output"
    input_a.mkdir()
    input_b.mkdir()

    black = np.zeros((2, 2, 3), dtype=np.uint8)
    green = np.zeros((2, 2, 3), dtype=np.uint8)
    green[:, :] = (0, 255, 0)

    assert cv2.imwrite(str(input_a / "frame.png"), black)
    assert cv2.imwrite(str(input_b / "frame.png"), green)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "blend",
            "-i",
            str(input_a),
            "-i",
            str(input_b),
            "-w",
            "0.5,0.5",
            "-o",
            str(output_dir),
            "--black-transparent",
            "true,false",
        ],
    )

    assert result.exit_code == 0, result.stdout

    saved = cv2.imread(str(output_dir / "frame.png"), cv2.IMREAD_COLOR)
    assert saved is not None
    assert tuple(int(channel) for channel in saved[0, 0]) == (0, 255, 0)
