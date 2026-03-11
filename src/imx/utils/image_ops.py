from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import numpy.typing as npt

ImageArray = npt.NDArray[np.uint8]
ImageLikeArray = npt.NDArray[np.generic]
ResizeMode = Literal["min", "max", "error"]


def load_image(path: Path, *, unchanged: bool = False) -> npt.NDArray[np.generic]:
    flag = cv2.IMREAD_UNCHANGED if unchanged else cv2.IMREAD_COLOR
    image = cv2.imread(str(path), flag)
    if image is None:
        raise ValueError(f"failed to load image: {path}")
    return image


def save_image(path: Path, image: ImageArray) -> None:
    if not cv2.imwrite(str(path), image):
        raise ValueError(f"failed to save image: {path}")


def parse_grid(value: str | None, count: int) -> tuple[int, int]:
    if value is None:
        rows = math.ceil(math.sqrt(count))
        cols = math.ceil(count / rows)
        return rows, cols

    normalized = value.lower().replace("x", " ")
    parts = normalized.split()
    if len(parts) != 2:
        raise ValueError("grid must be specified as HxW, for example 2x3")

    rows, cols = (int(part) for part in parts)
    if rows <= 0 or cols <= 0:
        raise ValueError("grid dimensions must be positive integers")
    return rows, cols


def ensure_same_size(images: list[ImageLikeArray]) -> tuple[int, int]:
    heights = {int(image.shape[0]) for image in images}
    widths = {int(image.shape[1]) for image in images}
    if len(heights) != 1 or len(widths) != 1:
        raise ValueError("image sizes do not match; use --resize min or --resize max")
    return images[0].shape[1], images[0].shape[0]


def resize_images(images: list[ImageLikeArray], mode: ResizeMode) -> list[ImageArray]:
    if not images:
        raise ValueError("no images provided")

    widths = [int(image.shape[1]) for image in images]
    heights = [int(image.shape[0]) for image in images]

    if mode == "error":
        ensure_same_size(images)
        return [to_bgr_uint8(image) for image in images]

    target_width = min(widths) if mode == "min" else max(widths)
    target_height = min(heights) if mode == "min" else max(heights)
    interpolation = cv2.INTER_AREA if mode == "min" else cv2.INTER_LINEAR

    return [
        cv2.resize(to_bgr_uint8(image), (target_width, target_height), interpolation=interpolation)
        for image in images
    ]


def add_title(image: ImageArray, title: str, margin: int) -> ImageArray:
    title_height = 36
    canvas = cv2.copyMakeBorder(
        image,
        title_height,
        0,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )
    cv2.putText(
        canvas,
        title,
        (12, title_height - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    if margin > 0:
        canvas = add_margin(canvas, 0, 0, margin, margin)
    return canvas


def add_margin(image: ImageArray, top: int, bottom: int, left: int, right: int) -> ImageArray:
    return cv2.copyMakeBorder(
        image,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )


def compose_grid(
    images: list[ImageArray],
    rows: int,
    cols: int,
    margin: int,
) -> ImageArray:
    if len(images) > rows * cols:
        raise ValueError("grid is smaller than the number of images")

    tile_height, tile_width = images[0].shape[:2]
    blank = np.zeros((tile_height, tile_width, 3), dtype=np.uint8)
    padded = images + [blank] * (rows * cols - len(images))

    grid_rows: list[ImageArray] = []
    for row_index in range(rows):
        row_tiles: list[ImageArray] = []
        for col_index in range(cols):
            tile = padded[row_index * cols + col_index]
            if col_index < cols - 1 and margin > 0:
                tile = add_margin(tile, 0, 0, 0, margin)
            row_tiles.append(tile)
        row = np.hstack(row_tiles)
        if row_index < rows - 1 and margin > 0:
            row = add_margin(row, 0, margin, 0, 0)
        grid_rows.append(row)
    return np.vstack(grid_rows)


def to_bgr_uint8(image: ImageLikeArray) -> ImageArray:
    clipped = np.clip(image, 0, 255).astype(np.uint8)
    if clipped.ndim == 2:
        return cv2.cvtColor(clipped, cv2.COLOR_GRAY2BGR)
    if clipped.ndim == 3 and clipped.shape[2] == 1:
        return cv2.cvtColor(clipped, cv2.COLOR_GRAY2BGR)
    if clipped.ndim == 3 and clipped.shape[2] == 3:
        return clipped
    raise ValueError(f"unsupported image shape: {clipped.shape}")


def normalize_to_uint8(image: ImageLikeArray, min_value: float, max_value: float) -> npt.NDArray[np.uint8]:
    source = image.astype(np.float32)
    if max_value <= min_value:
        return np.zeros(source.shape[:2], dtype=np.uint8)
    normalized = (source - min_value) / (max_value - min_value)
    scaled = np.clip(normalized * 255.0, 0, 255)
    return scaled.astype(np.uint8)


def apply_colormap(image: npt.NDArray[np.uint8], cmap: int) -> ImageArray:
    return cv2.applyColorMap(image, cmap)
