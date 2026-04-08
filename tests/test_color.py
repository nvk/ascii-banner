# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.color — ANSI color application."""

import pytest

from ascii_banner.color import apply, RESET, NAMED_COLORS, RAINBOW


SAMPLE = "Hello\nWorld"


# ---------------------------------------------------------------------------
# Named colors
# ---------------------------------------------------------------------------

class TestNamedColors:
    @pytest.mark.parametrize("name", list(NAMED_COLORS.keys()))
    def test_named_color_applied(self, name: str) -> None:
        result = apply(SAMPLE, name)
        assert NAMED_COLORS[name] in result
        assert RESET in result

    def test_case_insensitive(self) -> None:
        result = apply(SAMPLE, "RED")
        assert NAMED_COLORS["red"] in result

    def test_whitespace_stripped(self) -> None:
        result = apply(SAMPLE, "  green  ")
        assert NAMED_COLORS["green"] in result

    def test_unknown_color_passthrough(self) -> None:
        result = apply(SAMPLE, "notacolor")
        assert result == SAMPLE


# ---------------------------------------------------------------------------
# Hex colors
# ---------------------------------------------------------------------------

class TestHexColors:
    def test_hex_red(self) -> None:
        result = apply(SAMPLE, "#ff0000")
        assert "\033[38;2;255;0;0m" in result
        assert RESET in result

    def test_hex_green(self) -> None:
        result = apply(SAMPLE, "#00ff00")
        assert "\033[38;2;0;255;0m" in result

    def test_hex_blue(self) -> None:
        result = apply(SAMPLE, "#0000ff")
        assert "\033[38;2;0;0;255m" in result

    def test_hex_case_insensitive(self) -> None:
        result = apply(SAMPLE, "#FF8800")
        assert "\033[38;2;255;136;0m" in result

    def test_invalid_hex_passthrough(self) -> None:
        result = apply(SAMPLE, "#xyz")
        assert result == SAMPLE

    def test_short_hex_passthrough(self) -> None:
        result = apply(SAMPLE, "#abc")
        assert result == SAMPLE


# ---------------------------------------------------------------------------
# Rainbow
# ---------------------------------------------------------------------------

class TestRainbow:
    def test_rainbow_applies_codes(self) -> None:
        result = apply("ABCDEF", "rainbow")
        # Should contain at least some rainbow ANSI codes
        assert RESET in result
        rainbow_found = any(code in result for code in RAINBOW)
        assert rainbow_found

    def test_rainbow_multiline(self) -> None:
        result = apply(SAMPLE, "rainbow")
        lines = result.split("\n")
        assert len(lines) == 2

    def test_rainbow_preserves_spaces(self) -> None:
        result = apply("A B", "rainbow")
        # Spaces should not get color codes
        assert result.count(RESET) >= 2  # at least A and B get color+reset

    def test_rainbow_empty_line_preserved(self) -> None:
        result = apply("A\n\nB", "rainbow")
        lines = result.split("\n")
        assert lines[1] == ""


# ---------------------------------------------------------------------------
# Gradient
# ---------------------------------------------------------------------------

class TestGradient:
    def test_gradient_two_colors(self) -> None:
        result = apply("ABCDEF", "gradient:red:blue")
        assert RESET in result
        assert "\033[38;2;" in result

    def test_gradient_hex_colors(self) -> None:
        result = apply("ABCDEF", "gradient:#ff0000:#0000ff")
        assert RESET in result
        assert "\033[38;2;" in result

    def test_gradient_rainbow(self) -> None:
        result = apply("ABCDEF", "gradient:rainbow")
        assert RESET in result
        assert "\033[38;2;" in result

    def test_gradient_invalid_colors_passthrough(self) -> None:
        result = apply("ABCDEF", "gradient:notreal:alsonotreal")
        assert result == "ABCDEF"

    def test_gradient_wrong_format_passthrough(self) -> None:
        result = apply("ABCDEF", "gradient:")
        assert result == "ABCDEF"

    def test_gradient_multiline(self) -> None:
        result = apply(SAMPLE, "gradient:red:blue")
        lines = result.split("\n")
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestColorEdgeCases:
    def test_empty_string(self) -> None:
        result = apply("", "red")
        # Empty text should still work
        assert isinstance(result, str)

    def test_single_char(self) -> None:
        result = apply("X", "blue")
        assert NAMED_COLORS["blue"] in result
        assert RESET in result

    def test_empty_lines_not_colored(self) -> None:
        result = apply("A\n\nB", "red")
        lines = result.split("\n")
        # The empty line should remain empty
        assert lines[1] == ""
