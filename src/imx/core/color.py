from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt

from imx.utils.files import SortMode, ensure_output_dir, list_image_files
from imx.utils.image_ops import ImageArray, apply_colormap, load_image, normalize_to_uint8

DEFAULT_CMAP = "VIRIDIS"
DEFAULT_RANDOM_SEED = 0
ColorOverride = tuple[int, int, int, int]


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


def colorize_random_image(
    path: Path,
    overrides: list[ColorOverride] | None = None,
    seed: int = DEFAULT_RANDOM_SEED,
) -> ImageArray:
    image = load_image(path, unchanged=True)
    single = to_single_channel(image)
    discrete = to_discrete_values(single)
    unique_values, inverse = np.unique(discrete, return_inverse=True)
    palette = build_random_palette(unique_values, overrides=overrides, seed=seed)
    height, width = discrete.shape
    return palette[inverse].reshape(height, width, 3)


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


def validate_color_overrides(overrides: list[ColorOverride] | None) -> list[ColorOverride]:
    if overrides is None:
        return []

    seen: set[int] = set()
    validated: list[ColorOverride] = []
    for value, red, green, blue in overrides:
        if value < 0:
            raise ValueError("override values must be non-negative integers")
        for channel in (red, green, blue):
            if not 0 <= channel <= 255:
                raise ValueError("override colors must be in the range 0..255")
        if value in seen:
            raise ValueError(f"duplicate color override for value: {value}")
        seen.add(value)
        validated.append((value, red, green, blue))
    return validated


def to_discrete_values(image: npt.NDArray[np.generic]) -> npt.NDArray[np.int64]:
    if np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.bool_):
        return image.astype(np.int64)

    rounded = np.rint(image)
    if not np.allclose(image, rounded):
        raise ValueError("random colorize only supports integer-valued images; use --cmap for continuous values")
    return rounded.astype(np.int64)


def build_random_palette(
    unique_values: npt.NDArray[np.int64],
    overrides: list[ColorOverride] | None = None,
    seed: int = DEFAULT_RANDOM_SEED,
) -> ImageArray:
    validated = validate_color_overrides(overrides)
    override_map = {value: (blue, green, red) for value, red, green, blue in validated}

    palette = np.zeros((len(unique_values), 3), dtype=np.uint8)
    for index, value in enumerate(unique_values.tolist()):
        if value == 0:
            continue
        if value in override_map:
            palette[index] = np.array(override_map[value], dtype=np.uint8)
            continue

        palette[index] = random_color_for_value(value, seed=seed)
    return palette


def random_color_for_value(value: int, seed: int = DEFAULT_RANDOM_SEED) -> npt.NDArray[np.uint8]:
    value_int = int(value)
    sequence = np.random.SeedSequence(
        [
            seed,
            value_int & 0xFFFFFFFF,
            (value_int >> 32) & 0xFFFFFFFF,
        ]
    )
    rng = np.random.default_rng(sequence)
    color = rng.integers(0, 256, size=3, dtype=np.uint8)
    while int(color[0]) == 0 and int(color[1]) == 0 and int(color[2]) == 0:
        color = rng.integers(0, 256, size=3, dtype=np.uint8)
    return color
