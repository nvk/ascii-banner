# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.renderer — text rendering engine."""

import pytest

from ascii_banner.parser import load
from ascii_banner.renderer import render


@pytest.fixture()
def standard_font():
    return load("standard")


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------

class TestRenderBasic:
    def test_render_hi(self, standard_font) -> None:
        result = render(standard_font, "Hi")
        assert result, "Render should not return empty string"

    def test_render_multiline(self, standard_font) -> None:
        result = render(standard_font, "Hi")
        lines = result.split("\n")
        assert len(lines) == standard_font.height

    def test_render_nonempty_lines(self, standard_font) -> None:
        result = render(standard_font, "Hi")
        non_empty = [line for line in result.split("\n") if line.strip()]
        assert len(non_empty) > 0, "At least some lines should be non-empty"

    def test_render_empty_string(self, standard_font) -> None:
        result = render(standard_font, "")
        assert result == ""

    def test_render_single_char(self, standard_font) -> None:
        result = render(standard_font, "A")
        lines = result.split("\n")
        assert len(lines) == standard_font.height

    def test_render_space_only(self, standard_font) -> None:
        result = render(standard_font, " ")
        lines = result.split("\n")
        assert len(lines) == standard_font.height

    def test_render_hello_world(self, standard_font) -> None:
        result = render(standard_font, "Hello World")
        assert len(result) > 0
        lines = result.split("\n")
        assert len(lines) == standard_font.height


# ---------------------------------------------------------------------------
# Justification
# ---------------------------------------------------------------------------

class TestRenderJustify:
    def test_left_justify_default(self, standard_font) -> None:
        result = render(standard_font, "A", width=120, justify="left")
        lines = result.split("\n")
        # Left-justified: no extra padding added (font may have leading spaces in design)
        non_empty = [l for l in lines if l.strip()]
        assert len(non_empty) > 0

    def test_center_justify(self, standard_font) -> None:
        result = render(standard_font, "A", width=120, justify="center")
        lines = result.split("\n")
        non_empty = [l for l in lines if l.strip()]
        # Centered lines should have leading spaces
        assert any(l.startswith(" ") for l in non_empty)

    def test_right_justify(self, standard_font) -> None:
        result = render(standard_font, "A", width=120, justify="right")
        lines = result.split("\n")
        non_empty = [l for l in lines if l.strip()]
        # Right-justified lines should have leading spaces
        assert all(l.startswith(" ") for l in non_empty)

    def test_right_more_padding_than_center(self, standard_font) -> None:
        center = render(standard_font, "A", width=120, justify="center")
        right = render(standard_font, "A", width=120, justify="right")
        # Right justify should have more leading spaces than center
        center_pad = len(center.split("\n")[0]) - len(center.split("\n")[0].lstrip())
        right_pad = len(right.split("\n")[0]) - len(right.split("\n")[0].lstrip())
        # Only check on non-empty lines
        center_lines = [l for l in center.split("\n") if l.strip()]
        right_lines = [l for l in right.split("\n") if l.strip()]
        if center_lines and right_lines:
            c_pad = len(center_lines[0]) - len(center_lines[0].lstrip())
            r_pad = len(right_lines[0]) - len(right_lines[0].lstrip())
            assert r_pad >= c_pad

    def test_no_justify_without_width(self, standard_font) -> None:
        """With width=0, justify should have no effect."""
        left = render(standard_font, "Hi", width=0, justify="left")
        center = render(standard_font, "Hi", width=0, justify="center")
        assert left == center


# ---------------------------------------------------------------------------
# Different fonts
# ---------------------------------------------------------------------------

class TestRenderFonts:
    def test_big_font(self) -> None:
        font = load("Big")
        result = render(font, "OK")
        assert result
        assert len(result.split("\n")) == font.height

    def test_small_font(self) -> None:
        font = load("Small")
        result = render(font, "OK")
        assert result
        assert len(result.split("\n")) == font.height

    def test_banner_font(self) -> None:
        font = load("Banner")
        result = render(font, "OK")
        assert result
