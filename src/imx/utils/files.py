from __future__ import annotations

from pathlib import Path
from typing import Literal

from natsort import natsorted

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SortMode = Literal["nat", "lex"]


def list_image_files(directory: Path, sort_mode: SortMode = "nat") -> list[Path]:
    if not directory.exists():
        raise FileNotFoundError(f"input directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {directory}")

    files = [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
    if not files:
        raise FileNotFoundError(f"no image files found in: {directory}")

    if sort_mode == "nat":
        return natsorted(files, key=lambda path: path.name)
    return sorted(files, key=lambda path: path.name)


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
