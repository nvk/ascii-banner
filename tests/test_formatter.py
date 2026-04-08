# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.formatter — code comment formatting."""

import pytest

from ascii_banner.formatter import format_comment, list_formats, FORMATS


SAMPLE = "Hello\nWorld"


# ---------------------------------------------------------------------------
# Python comments
# ---------------------------------------------------------------------------

class TestPythonFormat:
    def test_python_prefix(self) -> None:
        result = format_comment(SAMPLE, "python")
        lines = result.split("\n")
        assert all(line.startswith("# ") for line in lines)

    def test_python_preserves_content(self) -> None:
        result = format_comment(SAMPLE, "python")
        assert "Hello" in result
        assert "World" in result


# ---------------------------------------------------------------------------
# JavaScript comments
# ---------------------------------------------------------------------------

class TestJsFormat:
    def test_js_prefix(self) -> None:
        result = format_comment(SAMPLE, "js")
        lines = result.split("\n")
        assert all(line.startswith("// ") for line in lines)

    def test_javascript_alias(self) -> None:
        result_js = format_comment(SAMPLE, "js")
        result_javascript = format_comment(SAMPLE, "javascript")
        assert result_js == result_javascript


# ---------------------------------------------------------------------------
# C block comments
# ---------------------------------------------------------------------------

class TestCFormat:
    def test_c_header(self) -> None:
        result = format_comment(SAMPLE, "c")
        lines = result.split("\n")
        assert lines[0] == "/*"

    def test_c_footer(self) -> None:
        result = format_comment(SAMPLE, "c")
        lines = result.split("\n")
        assert lines[-1] == " */"

    def test_c_prefix(self) -> None:
        result = format_comment(SAMPLE, "c")
        lines = result.split("\n")
        # Middle lines (not header/footer) should start with " * "
        for line in lines[1:-1]:
            assert line.startswith(" * ")


# ---------------------------------------------------------------------------
# HTML comments
# ---------------------------------------------------------------------------

class TestHtmlFormat:
    def test_html_header(self) -> None:
        result = format_comment(SAMPLE, "html")
        lines = result.split("\n")
        assert lines[0] == "<!--"

    def test_html_footer(self) -> None:
        result = format_comment(SAMPLE, "html")
        lines = result.split("\n")
        assert lines[-1] == "-->"

    def test_html_prefix(self) -> None:
        result = format_comment(SAMPLE, "html")
        lines = result.split("\n")
        for line in lines[1:-1]:
            assert line.startswith("  ")


# ---------------------------------------------------------------------------
# Other formats
# ---------------------------------------------------------------------------

class TestOtherFormats:
    def test_bash_prefix(self) -> None:
        result = format_comment("test", "bash")
        assert result.startswith("# ")

    def test_sql_prefix(self) -> None:
        result = format_comment("test", "sql")
        assert result.startswith("-- ")

    def test_go_prefix(self) -> None:
        result = format_comment("test", "go")
        assert result.startswith("// ")

    def test_unknown_format_passthrough(self) -> None:
        result = format_comment(SAMPLE, "brainfuck")
        assert result == SAMPLE

    def test_case_insensitive(self) -> None:
        result = format_comment(SAMPLE, "Python")
        lines = result.split("\n")
        assert all(line.startswith("# ") for line in lines)


# ---------------------------------------------------------------------------
# list_formats
# ---------------------------------------------------------------------------

class TestListFormats:
    def test_returns_list(self) -> None:
        fmts = list_formats()
        assert isinstance(fmts, list)

    def test_contains_expected(self) -> None:
        fmts = list_formats()
        for expected in ["python", "js", "c", "html", "bash", "go"]:
            assert expected in fmts

    def test_sorted(self) -> None:
        fmts = list_formats()
        assert fmts == sorted(fmts)

    def test_no_duplicates(self) -> None:
        fmts = list_formats()
        assert len(fmts) == len(set(fmts))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestFormatterEdgeCases:
    def test_empty_string(self) -> None:
        result = format_comment("", "python")
        assert result == "#"

    def test_empty_line_in_middle(self) -> None:
        result = format_comment("A\n\nB", "python")
        lines = result.split("\n")
        assert len(lines) == 3
        # Empty line should get prefix stripped of trailing space
        assert lines[1] == "#"

    def test_whitespace_in_format_name(self) -> None:
        result = format_comment("test", "  python  ")
        assert result.startswith("# ")
