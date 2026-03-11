from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt

from imx.utils.files import SortMode, ensure_output_dir, list_image_files
from imx.utils.image_ops import ImageArray, apply_colormap, load_image, normalize_to_uint8

DEFAULT_CMAP = "VIRIDIS"


def resolve_colormap(name: str | None) -> int:
    cmap_name = (name or DEFAULT_CMAP).upper()
    attr_name = f"COLORMAP_{cmap_name}"
    if not hasattr(cv2, attr_name):
        raise ValueError(f"unsupported colormap: {cmap_name}")
    return int(getattr(cv2, attr_name))


def collect_global_minmax(files: list[Path]) -> tuple[float, float]:
    mins: list[float] = []
    maxs: list[float] = []
    for path in files:
        image = load_image(path, unchanged=True)
        single = to_single_channel(image)
        mins.append(float(np.min(single)))
        maxs.append(float(np.max(single)))
    return min(mins), max(maxs)


def colorize_image(path: Path, min_value: float, max_value: float, cmap: int) -> ImageArray:
    image = load_image(path, unchanged=True)
    single = to_single_channel(image)
    normalized = normalize_to_uint8(single, min_value, max_value)
    return apply_colormap(normalized, cmap)


def prepare_output_files(input_dir: Path, output_dir: Path, sort_mode: SortMode = "nat") -> list[tuple[Path, Path]]:
    ensure_output_dir(output_dir)
    files = list_image_files(input_dir, sort_mode=sort_mode)
    return [(path, output_dir / path.name) for path in files]


def to_single_channel(image: npt.NDArray[np.generic]) -> npt.NDArray[np.generic]:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 1:
        return image[:, :, 0]
    raise ValueError("colorize only supports single-channel images")
