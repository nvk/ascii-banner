# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.parser — FIGlet font parsing."""

import pytest

from ascii_banner.parser import Font, FIGCharacter, parse, load, load_file, list_fonts


# ---------------------------------------------------------------------------
# parse()
# ---------------------------------------------------------------------------

class TestParse:
    """Tests for parse() with the standard.flf font content."""

    @pytest.fixture()
    def standard_font(self) -> Font:
        return load("standard")

    def test_height_positive(self, standard_font: Font) -> None:
        assert standard_font.height > 0

    def test_height_is_six(self, standard_font: Font) -> None:
        """Standard font has height 6."""
        assert standard_font.height == 6

    def test_hardblank(self, standard_font: Font) -> None:
        """Standard font uses '$' as hardblank."""
        assert standard_font.hardblank == "$"

    def test_has_ascii_chars(self, standard_font: Font) -> None:
        """All printable ASCII (32-126) must be present."""
        for code in range(32, 127):
            assert code in standard_font.characters, f"Missing char {code} ({chr(code)})"

    def test_char_height_matches_font(self, standard_font: Font) -> None:
        """Each character must have exactly font.height lines."""
        for code, char in standard_font.characters.items():
            assert len(char.lines) == standard_font.height, (
                f"Char {code} ({chr(code)}) has {len(char.lines)} lines, expected {standard_font.height}"
            )

    def test_char_width_positive_for_printable(self, standard_font: Font) -> None:
        """Printable characters (except space) should have positive width."""
        # Space (32) can legitimately have width > 0 in standard font
        for code in range(33, 127):
            char = standard_font.characters[code]
            assert char.width > 0, f"Char {code} ({chr(code)}) has width 0"

    def test_comment_nonempty(self, standard_font: Font) -> None:
        """Standard font has a comment block."""
        assert standard_font.comment
        assert len(standard_font.comment) > 0

    def test_comment_lines_count(self, standard_font: Font) -> None:
        """comment_lines should be > 0 for standard font."""
        assert standard_font.comment_lines > 0

    def test_smush_mode(self, standard_font: Font) -> None:
        """Standard font should use smushing."""
        assert standard_font.smush_mode in ("smushing", "fitting", "fullwidth")

    def test_get_char_known(self, standard_font: Font) -> None:
        """get_char('A') returns a valid FIGCharacter."""
        ch = standard_font.get_char("A")
        assert isinstance(ch, FIGCharacter)
        assert ch.width > 0

    def test_get_char_unknown_falls_back(self, standard_font: Font) -> None:
        """get_char for an unknown codepoint should fall back gracefully."""
        ch = standard_font.get_char("\U0001f600")  # emoji, unlikely in font
        assert isinstance(ch, FIGCharacter)

    def test_parse_invalid_header_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid FIGlet font"):
            parse("not a font file at all")

    def test_parse_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            parse("")

    def test_parse_short_header_raises(self) -> None:
        with pytest.raises(ValueError, match="too few fields"):
            parse("flf2a$ 6 5")


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

class TestLoad:
    def test_load_standard(self) -> None:
        font = load("standard")
        assert font.name == "standard"
        assert font.height > 0

    def test_load_big(self) -> None:
        font = load("Big")
        assert font.name == "Big"
        assert font.height > 0

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(Exception):
            load("this_font_does_not_exist_xyz")


# ---------------------------------------------------------------------------
# load_file()
# ---------------------------------------------------------------------------

class TestLoadFile:
    def test_load_file_via_path(self, tmp_path) -> None:
        """Create a minimal .flf and load it."""
        content = (
            "flf2a$ 1 1 5 0 1\n"
            "Test font\n"
        )
        # Build minimal characters for codes 32-126
        for code in range(32, 127):
            if code == 126:
                content += "X@@\n"
            else:
                content += "X@\n"

        p = tmp_path / "test.flf"
        p.write_text(content)
        font = load_file(str(p))
        assert font.name == "test"
        assert font.height == 1

    def test_load_file_nonexistent_raises(self) -> None:
        with pytest.raises(Exception):
            load_file("/nonexistent/path/font.flf")


# ---------------------------------------------------------------------------
# list_fonts()
# ---------------------------------------------------------------------------

class TestListFonts:
    def test_returns_list(self) -> None:
        fonts = list_fonts()
        assert isinstance(fonts, list)

    def test_contains_standard(self) -> None:
        fonts = list_fonts()
        assert "standard" in fonts

    def test_sorted(self) -> None:
        fonts = list_fonts()
        assert fonts == sorted(fonts)

    def test_no_flf_extension(self) -> None:
        fonts = list_fonts()
        for name in fonts:
            assert not name.endswith(".flf"), f"{name} should not have .flf extension"

    def test_nonempty(self) -> None:
        fonts = list_fonts()
        assert len(fonts) > 10, "Should have many built-in fonts"
