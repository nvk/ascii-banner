# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""ANSI terminal playback for ascii-banner animation frames."""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence
from typing import TextIO

from .animation import Frame
from .canvas import Canvas, Cell, RGB


RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[H\033[J"
ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"


def canvas_to_ansi(canvas: Canvas) -> str:
    """Serialize a canvas to ANSI text."""
    lines: list[str] = []
    for row in canvas.cells:
        parts: list[str] = []
        for cell in row:
            prefix = _style_prefix(cell)
            if prefix:
                parts.append(f"{prefix}{cell.char}{RESET}")
            else:
                parts.append(cell.char)
        lines.append("".join(parts).rstrip())
    return "\n".join(lines)


def render_static(canvas: Canvas) -> str:
    """Render a canvas once, preserving styles when present."""
    if canvas.has_style():
        return canvas_to_ansi(canvas)
    return canvas.to_text(trim=True)


def play(
    frames: Sequence[Frame],
    *,
    fps: int,
    loop: int = 1,
    stream: TextIO | None = None,
    alt_screen: bool = False,
) -> None:
    """Play frames in an ANSI terminal and restore terminal state on exit."""
    if not frames:
        return

    if fps <= 0:
        raise ValueError("fps must be greater than zero")
    if loop < 0:
        raise ValueError("loop must be zero or greater")

    out = stream or sys.stdout
    delay = 1 / fps
    loops_done = 0

    try:
        if alt_screen:
            out.write(ALT_SCREEN_ON)
        out.write(HIDE_CURSOR)
        while loop == 0 or loops_done < loop:
            for frame in frames:
                out.write(CLEAR)
                out.write(canvas_to_ansi(frame.canvas))
                out.flush()
                time.sleep(frame.delay_ms / 1000 if frame.delay_ms else delay)
            loops_done += 1
    finally:
        out.write(RESET)
        out.write(SHOW_CURSOR)
        if alt_screen:
            out.write(ALT_SCREEN_OFF)
        out.write("\n")
        out.flush()


def _style_prefix(cell: Cell) -> str:
    parts: list[str] = []
    if cell.bold:
        parts.append("1")
    if cell.fg is not None:
        parts.append(_fg_code(cell.fg))
    if cell.bg is not None:
        parts.append(_bg_code(cell.bg))
    if not parts:
        return ""
    return f"\033[{';'.join(parts)}m"


def _fg_code(rgb: RGB) -> str:
    return f"38;2;{rgb[0]};{rgb[1]};{rgb[2]}"


def _bg_code(rgb: RGB) -> str:
    return f"48;2;{rgb[0]};{rgb[1]};{rgb[2]}"
