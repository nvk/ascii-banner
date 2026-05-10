# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Media export for ascii-banner animation frames."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .animation import Frame
from .canvas import Canvas, RGB


class MediaExportError(RuntimeError):
    """Raised when media export cannot be completed."""


@dataclass(frozen=True)
class ExportOptions:
    fps: int
    loop: int = 1
    cell_width: int = 10
    cell_height: int = 18
    fg: RGB = (255, 255, 255)
    bg: RGB = (0, 0, 0)
    font_path: str | None = None


def export(frames: Sequence[Frame], path: str | Path, options: ExportOptions) -> None:
    """Export animation frames to GIF, WebP, MP4, or WebM."""
    if not frames:
        raise MediaExportError("no frames to export")
    if options.fps <= 0:
        raise MediaExportError("fps must be greater than zero")
    if options.loop < 0:
        raise MediaExportError("loop must be zero or greater")
    if options.cell_width <= 0 or options.cell_height <= 0:
        raise MediaExportError("cell dimensions must be greater than zero")

    output = Path(path)
    ext = output.suffix.lower()

    if ext == ".gif":
        _export_gif(frames, output, options)
        return
    if ext == ".webp":
        _export_webp(frames, output, options)
        return
    if ext in {".mp4", ".webm"}:
        _export_video(frames, output, options, ext)
        return

    raise MediaExportError(
        f"unsupported export format {ext!r}; use .gif, .mp4, .webm, or .webp"
    )


def rasterize(frame: Frame, options: ExportOptions):
    """Rasterize one frame to a Pillow Image."""
    Image, ImageDraw, ImageFont = _load_pillow()
    font = _load_font(ImageFont, options)
    canvas = frame.canvas
    width = max(1, canvas.width * options.cell_width)
    height = max(1, canvas.height * options.cell_height)
    image = Image.new("RGB", (width, height), options.bg)
    draw = ImageDraw.Draw(image)

    for y, row in enumerate(canvas.cells):
        for x, cell in enumerate(row):
            x0 = x * options.cell_width
            y0 = y * options.cell_height
            if cell.bg is not None:
                draw.rectangle(
                    [x0, y0, x0 + options.cell_width, y0 + options.cell_height],
                    fill=cell.bg,
                )
            if cell.char != " ":
                draw.text(
                    (x0, y0),
                    cell.char,
                    fill=cell.fg or options.fg,
                    font=font,
                )
    return image


def _export_gif(frames: Sequence[Frame], output: Path, options: ExportOptions) -> None:
    images = [rasterize(frame, options) for frame in frames]
    durations = [frame.delay_ms for frame in frames]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=options.loop,
        optimize=False,
    )


def _export_webp(frames: Sequence[Frame], output: Path, options: ExportOptions) -> None:
    images = [rasterize(frame, options) for frame in frames]
    durations = [frame.delay_ms for frame in frames]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=options.loop,
        format="WEBP",
    )


def _export_video(
    frames: Sequence[Frame],
    output: Path,
    options: ExportOptions,
    ext: str,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise MediaExportError("ffmpeg is required for MP4/WebM export")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ascii-banner-frames-") as temp:
        temp_dir = Path(temp)
        for index, frame in enumerate(frames):
            image = _pad_even(rasterize(frame, options), options.bg)
            image.save(temp_dir / f"frame_{index:05d}.png")

        pattern = str(temp_dir / "frame_%05d.png")
        if ext == ".mp4":
            cmd = [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                str(options.fps),
                "-i",
                pattern,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "18",
                "-preset",
                "veryfast",
                "-movflags",
                "+faststart",
                str(output),
            ]
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                str(options.fps),
                "-i",
                pattern,
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                "30",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or "ffmpeg failed"
            raise MediaExportError(message)


def _pad_even(image, bg: RGB):
    width, height = image.size
    even_width = width + (width % 2)
    even_height = height + (height % 2)
    if (even_width, even_height) == (width, height):
        return image

    Image, _ImageDraw, _ImageFont = _load_pillow()
    padded = Image.new("RGB", (even_width, even_height), bg)
    padded.paste(image, (0, 0))
    return padded


def _load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ModuleNotFoundError as exc:
        raise MediaExportError(
            "Pillow is required for media export; install with "
            "pip install 'ascii-banner[media]'"
        ) from exc
    return Image, ImageDraw, ImageFont


def _load_font(ImageFont, options: ExportOptions):
    size = max(1, int(options.cell_height * 0.90))
    if options.font_path:
        try:
            return ImageFont.truetype(options.font_path, size=size)
        except OSError as exc:
            raise MediaExportError(f"could not load media font: {options.font_path}") from exc

    candidates = (
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()
