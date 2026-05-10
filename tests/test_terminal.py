# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.terminal."""

from io import StringIO

from ascii_banner.animation import Frame
from ascii_banner.canvas import Canvas, apply_color
from ascii_banner.terminal import (
    CLEAR,
    HIDE_CURSOR,
    RESET,
    SHOW_CURSOR,
    canvas_to_ansi,
    play,
)


def test_canvas_to_ansi_serializes_truecolor() -> None:
    canvas = apply_color(Canvas.from_text("X"), "red")

    result = canvas_to_ansi(canvas)

    assert "\033[38;2;255;0;0mX" in result
    assert RESET in result


def test_play_restores_terminal_state(monkeypatch) -> None:
    monkeypatch.setattr("ascii_banner.terminal.time.sleep", lambda _seconds: None)
    stream = StringIO()
    frame = Frame(Canvas.from_text("X"), delay_ms=1)

    play([frame], fps=1, stream=stream)

    output = stream.getvalue()
    assert HIDE_CURSOR in output
    assert CLEAR in output
    assert SHOW_CURSOR in output
    assert RESET in output
