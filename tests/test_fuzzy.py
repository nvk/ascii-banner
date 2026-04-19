# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.fuzzy — fuzzy font name matching."""

import pytest

from ascii_banner.fuzzy import fuzzy_match
from ascii_banner.parser import list_fonts


@pytest.fixture()
def all_fonts() -> list[str]:
    return list_fonts()


# ---------------------------------------------------------------------------
# Exact match
# ---------------------------------------------------------------------------

class TestExactMatch:
    def test_exact_match(self, all_fonts) -> None:
        result = fuzzy_match("standard", all_fonts)
        assert result == ["standard"]

    def test_exact_case_insensitive(self, all_fonts) -> None:
        result = fuzzy_match("Standard", all_fonts)
        assert len(result) == 1
        assert result[0].lower() == "standard"

    def test_exact_match_big(self, all_fonts) -> None:
        result = fuzzy_match("Big", all_fonts)
        # list_fonts returns lowercase "big" for this font
        assert result[0].lower() == "big"


# ---------------------------------------------------------------------------
# Substring match
# ---------------------------------------------------------------------------

class TestSubstringMatch:
    def test_substring_beginning(self, all_fonts) -> None:
        result = fuzzy_match("stand", all_fonts)
        assert any("standard" in r.lower() for r in result)

    def test_substring_middle(self, all_fonts) -> None:
        result = fuzzy_match("anner", all_fonts)
        assert any("banner" in r.lower() for r in result)

    def test_max_results_respected(self, all_fonts) -> None:
        result = fuzzy_match("a", all_fonts, max_results=3)
        assert len(result) <= 3


# ---------------------------------------------------------------------------
# Typo tolerance
# ---------------------------------------------------------------------------

class TestTypoTolerance:
    def test_minor_typo(self, all_fonts) -> None:
        result = fuzzy_match("standrd", all_fonts)
        assert len(result) > 0
        # Should find "standard" or similar
        assert any("standard" in r.lower() for r in result)

    def test_single_char_off(self, all_fonts) -> None:
        result = fuzzy_match("standarx", all_fonts)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# No match
# ---------------------------------------------------------------------------

class TestNoMatch:
    def test_completely_wrong(self, all_fonts) -> None:
        result = fuzzy_match("zzzzzzzzzzzzzzzzz", all_fonts)
        assert result == []

    def test_empty_candidates(self) -> None:
        result = fuzzy_match("standard", [])
        assert result == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestFuzzyEdgeCases:
    def test_single_candidate(self) -> None:
        result = fuzzy_match("foo", ["foo"])
        assert result == ["foo"]

    def test_returns_list(self, all_fonts) -> None:
        result = fuzzy_match("big", all_fonts)
        assert isinstance(result, list)

    def test_max_results_default(self, all_fonts) -> None:
        result = fuzzy_match("a", all_fonts)
        assert len(result) <= 5
