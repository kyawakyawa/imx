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


def collect_image_sequences(input_dirs: list[Path], sort_mode: SortMode) -> list[list[Path]]:
    return [list_image_files(directory, sort_mode=sort_mode) for directory in input_dirs]


def blend_images(images: list[np.ndarray], weights: list[float], resize_mode: ResizeMode) -> ImageArray:
    prepared = resize_images(images, resize_mode)
    stack = np.stack([image.astype(np.float32) for image in prepared], axis=0)
    weight_array = np.asarray(weights, dtype=np.float32).reshape((-1, 1, 1, 1))
    blended = np.sum(stack * weight_array, axis=0)
    return np.clip(blended, 0, 255).astype(np.uint8)


def load_frame_set(paths: list[Path]) -> list[np.ndarray]:
    return [load_image(path, unchanged=False) for path in paths]
