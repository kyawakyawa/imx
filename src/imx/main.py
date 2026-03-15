from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import cv2
import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn

from imx.core.blend import collect_image_sequences, load_frame_set, parse_weights, prepare_weights, blend_images
from imx.core.color import (
    ColorOverride,
    collect_global_minmax,
    colorize_image,
    colorize_random_image,
    prepare_output_files,
    resolve_colormap,
    validate_color_overrides,
)
from imx.core.video import aligned_frame_count, build_grid_frame, codec_fourcc, collect_gif_frames, collect_sources, write_gif
from imx.utils.files import ensure_output_dir
from imx.utils.image_ops import save_image

app = typer.Typer(help="Image X-tool CLI")
console = Console()


class SortChoice(str, Enum):
    nat = "nat"
    lex = "lex"


class ResizeChoice(str, Enum):
    min = "min"
    max = "max"
    error = "error"


class CodecChoice(str, Enum):
    mp4v = "mp4v"
    h264 = "h264"


class WeightModeChoice(str, Enum):
    normalize = "normalize"
    keep = "keep"


class GifModeChoice(str, Enum):
    concat = "concat"
    interleave = "interleave"


def progress_bar() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def parse_force_color_args(args: list[str]) -> list[ColorOverride]:
    overrides: list[ColorOverride] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token != "--force-color":
            raise typer.BadParameter(f"unknown extra argument: {token}")
        if index + 4 >= len(args):
            raise typer.BadParameter("--force-color requires 4 integers: X R G B")

        values = args[index + 1 : index + 5]
        try:
            override = tuple(int(value) for value in values)
        except ValueError as error:
            raise typer.BadParameter("--force-color requires integer values") from error
        overrides.append(override)
        index += 5
    return validate_color_overrides(overrides)


@app.command()
def video(
    input: Annotated[list[Path], typer.Option("--input", "-i", exists=True, file_okay=False, dir_okay=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("output.mp4"),
    sort: Annotated[SortChoice, typer.Option("--sort")] = SortChoice.nat,
    grid: Annotated[str | None, typer.Option("--grid")] = None,
    title: Annotated[bool, typer.Option("--title")] = False,
    margin: Annotated[int, typer.Option("--margin")] = 0,
    resize: Annotated[ResizeChoice, typer.Option("--resize")] = ResizeChoice.error,
    codec: Annotated[CodecChoice, typer.Option("--codec")] = CodecChoice.mp4v,
    fps: Annotated[int, typer.Option("--fps")] = 10,
) -> None:
    if not input:
        raise typer.BadParameter("at least one --input is required")

    sources = collect_sources(input, sort_mode=sort.value)
    frame_count, has_mismatch = aligned_frame_count(sources)
    if has_mismatch:
        console.print(f"[yellow]warning:[/yellow] file counts differ; using shortest sequence ({frame_count} frames)")

    first_paths = [source.files[0] for source in sources]
    frame = build_grid_frame(first_paths, [source.directory.name for source in sources], resize.value, grid, title, margin)
    height, width = frame.shape[:2]

    writer = cv2.VideoWriter(str(output), codec_fourcc(codec.value), float(fps), (width, height))
    if not writer.isOpened():
        raise typer.BadParameter(f"failed to open video writer for codec={codec.value} output={output}")

    with progress_bar() as progress:
        task = progress.add_task("writing video", total=frame_count)
        for index in range(frame_count):
            frame_paths = [source.files[index] for source in sources]
            frame = build_grid_frame(
                frame_paths,
                [source.directory.name for source in sources],
                resize.value,
                grid,
                title,
                margin,
            )
            writer.write(frame)
            progress.advance(task)
    writer.release()
    console.print(f"saved video: {output}")


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Colorize single-channel images. Extra option: --force-color X R G B (repeatable).",
)
def colorize(
    ctx: typer.Context,
    input: Annotated[Path, typer.Option("--input", "-i", exists=True, file_okay=False, dir_okay=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("colorized"),
    cmap: Annotated[str | None, typer.Option("--cmap")] = None,
    sort: Annotated[SortChoice, typer.Option("--sort")] = SortChoice.nat,
) -> None:
    file_pairs = prepare_output_files(input, output, sort_mode=sort.value)
    try:
        overrides = parse_force_color_args(ctx.args)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    min_value = max_value = 0.0
    cmap_value: int | None = None
    if cmap is not None:
        min_value, max_value = collect_global_minmax([src for src, _ in file_pairs])
        try:
            cmap_value = resolve_colormap(cmap)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error

    with progress_bar() as progress:
        task = progress.add_task("colorizing", total=len(file_pairs))
        for src, dst in file_pairs:
            if cmap_value is None:
                colored = colorize_random_image(src, overrides=overrides)
            else:
                colored = colorize_image(src, min_value, max_value, cmap_value)
            save_image(dst, colored)
            progress.advance(task)
    console.print(f"saved colorized images to: {output}")


@app.command()
def blend(
    input: Annotated[list[Path], typer.Option("--input", "-i", exists=True, file_okay=False, dir_okay=True)],
    weights: Annotated[str, typer.Option("--weights", "-w")],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("blended"),
    sort: Annotated[SortChoice, typer.Option("--sort")] = SortChoice.nat,
    resize: Annotated[ResizeChoice, typer.Option("--resize")] = ResizeChoice.error,
    weight_mode: Annotated[WeightModeChoice, typer.Option("--weight-mode")] = WeightModeChoice.normalize,
) -> None:
    if not input:
        raise typer.BadParameter("at least one --input is required")

    raw_weights = parse_weights(weights)
    if len(raw_weights) != len(input):
        raise typer.BadParameter("number of weights must match number of input directories")

    prepared_weights, warned = prepare_weights(raw_weights, weight_mode.value)
    if warned:
        if weight_mode is WeightModeChoice.normalize:
            console.print("[yellow]warning:[/yellow] weights did not sum to 1, normalized automatically")
        else:
            console.print("[yellow]warning:[/yellow] weights do not sum to 1, using them as provided")

    ensure_output_dir(output)
    sequences = collect_image_sequences(input, sort_mode=sort.value)
    frame_count = min(len(sequence) for sequence in sequences)
    if len({len(sequence) for sequence in sequences}) > 1:
        console.print(f"[yellow]warning:[/yellow] file counts differ; using shortest sequence ({frame_count} frames)")

    with progress_bar() as progress:
        task = progress.add_task("blending", total=frame_count)
        for index in range(frame_count):
            frame_paths = [sequence[index] for sequence in sequences]
            images = load_frame_set(frame_paths)
            blended = blend_images(images, prepared_weights, resize.value)
            save_image(output / frame_paths[0].name, blended)
            progress.advance(task)
    console.print(f"saved blended images to: {output}")


@app.command()
def gif(
    input: Annotated[list[Path], typer.Option("--input", "-i", exists=True, file_okay=False, dir_okay=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("output.gif"),
    duration: Annotated[int, typer.Option("--duration", "-d")] = 100,
    sort: Annotated[SortChoice, typer.Option("--sort")] = SortChoice.nat,
    resize: Annotated[ResizeChoice, typer.Option("--resize")] = ResizeChoice.error,
    multi_mode: Annotated[GifModeChoice, typer.Option("--multi-mode")] = GifModeChoice.concat,
) -> None:
    if not input:
        raise typer.BadParameter("at least one --input is required")

    sources = collect_sources(input, sort_mode=sort.value)
    frames, has_mismatch = collect_gif_frames(sources, multi_mode.value, resize.value)
    if has_mismatch:
        console.print("[yellow]warning:[/yellow] file counts differ; interleave mode uses shortest sequence")

    write_gif(frames, output, duration)
    console.print(f"saved gif: {output}")


def run() -> None:
    app()


if __name__ == "__main__":
    run()
