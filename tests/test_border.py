# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.border — box border wrapping."""

import pytest

from ascii_banner.border import wrap, list_styles, STYLES


SAMPLE = "Hello\nWorld"


# ---------------------------------------------------------------------------
# Individual border styles
# ---------------------------------------------------------------------------

class TestSingleBorder:
    def test_corners(self) -> None:
        result = wrap(SAMPLE, "single")
        lines = result.split("\n")
        assert lines[0][0] == "\u250c"  # top-left
        assert lines[0][-1] == "\u2510"  # top-right
        assert lines[-1][0] == "\u2514"  # bottom-left
        assert lines[-1][-1] == "\u2518"  # bottom-right

    def test_horizontal_border(self) -> None:
        result = wrap(SAMPLE, "single")
        lines = result.split("\n")
        # Top line between corners should be \u2500
        assert all(c == "\u2500" for c in lines[0][1:-1])

    def test_vertical_sides(self) -> None:
        result = wrap(SAMPLE, "single")
        lines = result.split("\n")
        for line in lines[1:-1]:
            assert line[0] == "\u2502"
            assert line[-1] == "\u2502"


class TestDoubleBorder:
    def test_corners(self) -> None:
        result = wrap(SAMPLE, "double")
        lines = result.split("\n")
        assert lines[0][0] == "\u2554"
        assert lines[0][-1] == "\u2557"
        assert lines[-1][0] == "\u255a"
        assert lines[-1][-1] == "\u255d"

    def test_horizontal_border(self) -> None:
        result = wrap(SAMPLE, "double")
        lines = result.split("\n")
        assert all(c == "\u2550" for c in lines[0][1:-1])


class TestRoundedBorder:
    def test_corners(self) -> None:
        result = wrap(SAMPLE, "rounded")
        lines = result.split("\n")
        assert lines[0][0] == "\u256d"
        assert lines[0][-1] == "\u256e"
        assert lines[-1][0] == "\u2570"
        assert lines[-1][-1] == "\u256f"


class TestHeavyBorder:
    def test_corners(self) -> None:
        result = wrap(SAMPLE, "heavy")
        lines = result.split("\n")
        assert lines[0][0] == "\u250f"
        assert lines[0][-1] == "\u2513"
        assert lines[-1][0] == "\u2517"
        assert lines[-1][-1] == "\u251b"

    def test_heavy_lines(self) -> None:
        result = wrap(SAMPLE, "heavy")
        lines = result.split("\n")
        assert all(c == "\u2501" for c in lines[0][1:-1])


class TestAsciiBorder:
    def test_corners(self) -> None:
        result = wrap(SAMPLE, "ascii")
        lines = result.split("\n")
        assert lines[0][0] == "+"
        assert lines[0][-1] == "+"
        assert lines[-1][0] == "+"
        assert lines[-1][-1] == "+"

    def test_dashes(self) -> None:
        result = wrap(SAMPLE, "ascii")
        lines = result.split("\n")
        assert all(c == "-" for c in lines[0][1:-1])

    def test_pipes(self) -> None:
        result = wrap(SAMPLE, "ascii")
        lines = result.split("\n")
        for line in lines[1:-1]:
            assert line[0] == "|"
            assert line[-1] == "|"


# ---------------------------------------------------------------------------
# General behavior
# ---------------------------------------------------------------------------

class TestBorderGeneral:
    def test_line_count(self) -> None:
        """Border adds top + bottom = 2 extra lines."""
        result = wrap(SAMPLE, "single")
        input_lines = SAMPLE.split("\n")
        output_lines = result.split("\n")
        assert len(output_lines) == len(input_lines) + 2

    def test_content_preserved(self) -> None:
        result = wrap(SAMPLE, "single")
        assert "Hello" in result
        assert "World" in result

    def test_padding(self) -> None:
        """Default padding=1 means at least one space between content and border."""
        result = wrap("X", "single")
        lines = result.split("\n")
        # Content line should be: border + space + content + space + border
        content_line = lines[1]
        assert content_line[1] == " "  # padding after left border
        assert content_line[-2] == " "  # padding before right border

    def test_unknown_style_passthrough(self) -> None:
        result = wrap(SAMPLE, "nonexistent")
        assert result == SAMPLE

    def test_single_line_input(self) -> None:
        result = wrap("Hello", "ascii")
        lines = result.split("\n")
        assert len(lines) == 3  # top + content + bottom

    @pytest.mark.parametrize("style", list(STYLES.keys()))
    def test_all_styles_produce_output(self, style: str) -> None:
        result = wrap(SAMPLE, style)
        assert len(result) > len(SAMPLE)


# ---------------------------------------------------------------------------
# list_styles
# ---------------------------------------------------------------------------

class TestListStyles:
    def test_returns_list(self) -> None:
        styles = list_styles()
        assert isinstance(styles, list)

    def test_contains_expected(self) -> None:
        styles = list_styles()
        for expected in ["single", "double", "rounded", "heavy", "ascii"]:
            assert expected in styles

    def test_sorted(self) -> None:
        styles = list_styles()
        assert styles == sorted(styles)
