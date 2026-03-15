from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

from imx.utils.files import SortMode, list_image_files
from imx.utils.image_ops import ImageArray, ResizeMode, load_image, resize_images

WeightMode = Literal["normalize", "keep"]


def parse_weights(raw: str) -> list[float]:
    weights = [float(part.strip()) for part in raw.split(",") if part.strip()]
    if not weights:
        raise ValueError("weights must not be empty")
    return weights


def prepare_weights(weights: list[float], mode: WeightMode) -> tuple[list[float], bool]:
    total = sum(weights)
    if total == 0:
        raise ValueError("sum of weights must not be zero")
    if mode == "normalize" and not np.isclose(total, 1.0):
        return [weight / total for weight in weights], True
    return weights, not np.isclose(total, 1.0)


def parse_black_transparent_flags(raw: str | None, expected_count: int) -> list[bool]:
    if raw is None:
        return [False] * expected_count

    tokens = [part.strip().lower() for part in raw.split(",")]
    if len(tokens) != expected_count:
        raise ValueError("number of --black-transparent flags must match number of input directories")

    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsy = {"0", "false", "f", "no", "n", "off"}
    flags: list[bool] = []
    for token in tokens:
        if token in truthy:
            flags.append(True)
        elif token in falsy:
            flags.append(False)
        else:
            raise ValueError(f"invalid --black-transparent value: {token}")
    return flags


def collect_image_sequences(input_dirs: list[Path], sort_mode: SortMode) -> list[list[Path]]:
    return [list_image_files(directory, sort_mode=sort_mode) for directory in input_dirs]


def blend_images(
    images: list[np.ndarray],
    weights: list[float],
    resize_mode: ResizeMode,
    black_transparent_flags: list[bool] | None = None,
) -> ImageArray:
    prepared = resize_images(images, resize_mode)
    if black_transparent_flags is None:
        black_transparent_flags = [False] * len(prepared)
    if len(black_transparent_flags) != len(prepared):
        raise ValueError("number of black transparency flags must match number of images")

    stack = np.stack([image.astype(np.float32) for image in prepared], axis=0)
    weight_array = np.asarray(weights, dtype=np.float32).reshape((-1, 1, 1, 1))
    mask_layers = []
    for image, enabled in zip(prepared, black_transparent_flags, strict=True):
        if enabled:
            opaque = np.any(image != 0, axis=2, keepdims=True).astype(np.float32)
        else:
            opaque = np.ones((*image.shape[:2], 1), dtype=np.float32)
        mask_layers.append(opaque)

    mask_stack = np.stack(mask_layers, axis=0)
    effective_weights = weight_array * mask_stack
    total_weights = np.sum(effective_weights, axis=0)
    safe_total_weights = np.where(total_weights == 0, 1.0, total_weights)
    blended = np.sum(stack * effective_weights, axis=0) / safe_total_weights
    blended[total_weights.squeeze(axis=2) == 0] = 0
    return np.clip(blended, 0, 255).astype(np.uint8)


def load_frame_set(paths: list[Path]) -> list[np.ndarray]:
    return [load_image(path, unchanged=False) for path in paths]
