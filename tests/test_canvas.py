# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.canvas."""

from ascii_banner.canvas import Canvas, apply_color, parse_rgb


def test_canvas_from_text_pads_to_fixed_width() -> None:
    canvas = Canvas.from_text("A\nBC")

    assert canvas.width == 2
    assert canvas.height == 2
    assert canvas.to_lines() == ["A ", "BC"]
    assert canvas.to_lines(trim=True) == ["A", "BC"]


def test_canvas_empty_text_has_zero_dimensions() -> None:
    canvas = Canvas.from_text("")

    assert canvas.width == 0
    assert canvas.height == 0
    assert canvas.to_text() == ""


def test_parse_rgb_named_and_hex() -> None:
    assert parse_rgb("red") == (255, 0, 0)
    assert parse_rgb("#00ff88") == (0, 255, 136)
    assert parse_rgb("not-a-color") is None


def test_apply_solid_color_does_not_insert_ansi() -> None:
    canvas = apply_color(Canvas.from_text("A B"), "green")

    assert canvas.to_text() == "A B"
    assert canvas.cells[0][0].fg == (0, 255, 0)
    assert canvas.cells[0][1].fg is None
    assert canvas.cells[0][2].fg == (0, 255, 0)


def test_apply_gradient_color_changes_visible_cells() -> None:
    canvas = apply_color(Canvas.from_text("ABC"), "gradient:red:blue")

    assert canvas.cells[0][0].fg == (255, 0, 0)
    assert canvas.cells[0][2].fg == (0, 0, 255)
    assert "\033[" not in canvas.to_text()


def test_unknown_color_is_passthrough() -> None:
    original = Canvas.from_text("ABC")
    result = apply_color(original, "not-a-color")

    assert result == original
