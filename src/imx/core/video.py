from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image

from imx.utils.files import SortMode, list_image_files
from imx.utils.image_ops import (
    ImageArray,
    ResizeMode,
    add_title,
    compose_grid,
    load_image,
    parse_grid,
    resize_images,
)

GifMode = Literal["concat", "interleave"]


@dataclass(frozen=True)
class FrameSource:
    directory: Path
    files: list[Path]


def collect_sources(input_dirs: list[Path], sort_mode: SortMode) -> list[FrameSource]:
    return [FrameSource(directory=directory, files=list_image_files(directory, sort_mode=sort_mode)) for directory in input_dirs]


def aligned_frame_count(sources: list[FrameSource]) -> tuple[int, bool]:
    lengths = [len(source.files) for source in sources]
    if not lengths:
        raise ValueError("no input sources provided")
    target = min(lengths)
    return target, len(set(lengths)) > 1


def build_grid_frame(
    paths: list[Path],
    titles: list[str],
    resize_mode: ResizeMode,
    grid: str | None,
    with_title: bool,
    margin: int,
) -> ImageArray:
    loaded = [load_image(path, unchanged=False) for path in paths]
    prepared = resize_images(loaded, resize_mode)
    if with_title:
        prepared = [add_title(image, title, 0) for image, title in zip(prepared, titles, strict=True)]
    rows, cols = parse_grid(grid, len(prepared))
    return compose_grid(prepared, rows=rows, cols=cols, margin=margin)


def codec_fourcc(codec: str) -> int:
    if codec == "h264":
        return cv2.VideoWriter_fourcc(*"avc1")
    if codec == "mp4v":
        return cv2.VideoWriter_fourcc(*"mp4v")
    raise ValueError(f"unsupported codec: {codec}")


def write_gif(frames: list[ImageArray], output: Path, duration_ms: int) -> None:
    if not frames:
        raise ValueError("no frames to write")
    pil_frames = [Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) for frame in frames]
    pil_frames[0].save(
        output,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
    )


def collect_gif_frames(
    sources: list[FrameSource],
    mode: GifMode,
    resize_mode: ResizeMode,
) -> tuple[list[ImageArray], bool]:
    frame_mismatch = False
    if mode == "concat":
        loaded_frames: list[np.ndarray] = []
        for source in sources:
            for path in source.files:
                loaded_frames.append(load_image(path, unchanged=False))
        frames = resize_images(loaded_frames, resize_mode)
        return frames, frame_mismatch

    lengths = [len(source.files) for source in sources]
    target = min(lengths)
    frame_mismatch = len(set(lengths)) > 1
    loaded_frames: list[np.ndarray] = []
    for index in range(target):
        batch = [load_image(source.files[index], unchanged=False) for source in sources]
        loaded_frames.extend(batch)
    frames = resize_images(loaded_frames, resize_mode)
    return frames, frame_mismatch
