# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.smushing — FIGlet horizontal smushing rules."""

import pytest

from ascii_banner.smushing import (
    SM_EQUAL,
    SM_LOWLINE,
    SM_HIERARCHY,
    SM_PAIR,
    SM_BIGX,
    SM_HARDBLANK,
    smush_chars,
    calc_smush_amount,
)


HARDBLANK = "$"


# ---------------------------------------------------------------------------
# Space handling (universal)
# ---------------------------------------------------------------------------

class TestSmushCharsSpaces:
    def test_left_space_returns_right(self) -> None:
        assert smush_chars(" ", "X", 0, HARDBLANK) == "X"

    def test_right_space_returns_left(self) -> None:
        assert smush_chars("X", " ", 0, HARDBLANK) == "X"

    def test_both_spaces(self) -> None:
        assert smush_chars(" ", " ", 0, HARDBLANK) == " "


# ---------------------------------------------------------------------------
# Rule 1: Equal character (SM_EQUAL = 1)
# ---------------------------------------------------------------------------

class TestSmushRule1Equal:
    def test_equal_chars_smush(self) -> None:
        assert smush_chars("X", "X", SM_EQUAL, HARDBLANK) == "X"

    def test_equal_pipe(self) -> None:
        assert smush_chars("|", "|", SM_EQUAL, HARDBLANK) == "|"

    def test_unequal_chars_no_smush(self) -> None:
        assert smush_chars("X", "Y", SM_EQUAL, HARDBLANK) is None


# ---------------------------------------------------------------------------
# Rule 2: Underscore (SM_LOWLINE = 2)
# ---------------------------------------------------------------------------

class TestSmushRule2Lowline:
    def test_underscore_left_replaced(self) -> None:
        assert smush_chars("_", "|", SM_LOWLINE, HARDBLANK) == "|"

    def test_underscore_right_replaced(self) -> None:
        assert smush_chars("[", "_", SM_LOWLINE, HARDBLANK) == "["

    def test_underscore_with_slash(self) -> None:
        assert smush_chars("_", "/", SM_LOWLINE, HARDBLANK) == "/"

    def test_underscore_with_backslash(self) -> None:
        assert smush_chars("\\", "_", SM_LOWLINE, HARDBLANK) == "\\"

    def test_no_underscore_no_smush(self) -> None:
        assert smush_chars("X", "Y", SM_LOWLINE, HARDBLANK) is None


# ---------------------------------------------------------------------------
# Rule 3: Hierarchy (SM_HIERARCHY = 4)
# ---------------------------------------------------------------------------

class TestSmushRule3Hierarchy:
    def test_pipe_vs_slash(self) -> None:
        # | is class 1, / is class 2 -> higher class wins
        assert smush_chars("|", "/", SM_HIERARCHY, HARDBLANK) == "/"

    def test_bracket_vs_paren(self) -> None:
        # [ is class 3, ( is class 5 -> ( wins
        assert smush_chars("[", "(", SM_HIERARCHY, HARDBLANK) == "("

    def test_angle_vs_pipe(self) -> None:
        # > is class 6, | is class 1 -> > wins
        assert smush_chars(">", "|", SM_HIERARCHY, HARDBLANK) == ">"

    def test_same_class_no_smush(self) -> None:
        # [ and ] are both class 3
        assert smush_chars("[", "]", SM_HIERARCHY, HARDBLANK) is None

    def test_non_hierarchy_chars(self) -> None:
        assert smush_chars("X", "Y", SM_HIERARCHY, HARDBLANK) is None


# ---------------------------------------------------------------------------
# Rule 4: Opposite pair (SM_PAIR = 8)
# ---------------------------------------------------------------------------

class TestSmushRule4Pair:
    def test_brackets(self) -> None:
        assert smush_chars("[", "]", SM_PAIR, HARDBLANK) == "|"

    def test_braces(self) -> None:
        assert smush_chars("{", "}", SM_PAIR, HARDBLANK) == "|"

    def test_parens(self) -> None:
        assert smush_chars("(", ")", SM_PAIR, HARDBLANK) == "|"

    def test_reverse_brackets(self) -> None:
        assert smush_chars("]", "[", SM_PAIR, HARDBLANK) == "|"

    def test_non_pair(self) -> None:
        assert smush_chars("[", "(", SM_PAIR, HARDBLANK) is None


# ---------------------------------------------------------------------------
# Rule 5: Big X (SM_BIGX = 16)
# ---------------------------------------------------------------------------

class TestSmushRule5BigX:
    def test_slash_backslash(self) -> None:
        assert smush_chars("/", "\\", SM_BIGX, HARDBLANK) == "|"

    def test_backslash_slash(self) -> None:
        assert smush_chars("\\", "/", SM_BIGX, HARDBLANK) == "Y"

    def test_angle_brackets(self) -> None:
        assert smush_chars(">", "<", SM_BIGX, HARDBLANK) == "X"

    def test_non_bigx(self) -> None:
        assert smush_chars("<", ">", SM_BIGX, HARDBLANK) is None


# ---------------------------------------------------------------------------
# Rule 6: Hardblank (SM_HARDBLANK = 32)
# ---------------------------------------------------------------------------

class TestSmushRule6Hardblank:
    def test_both_hardblanks(self) -> None:
        assert smush_chars("$", "$", SM_HARDBLANK, "$") == "$"

    def test_one_hardblank_blocked(self) -> None:
        # One hardblank + non-hardblank -> always None
        assert smush_chars("$", "X", SM_HARDBLANK, "$") is None
        assert smush_chars("X", "$", SM_HARDBLANK, "$") is None

    def test_both_hardblanks_no_rule(self) -> None:
        # Both hardblanks but rule not set -> None
        assert smush_chars("$", "$", 0, "$") is None


# ---------------------------------------------------------------------------
# Universal smushing (rules == 0)
# ---------------------------------------------------------------------------

class TestSmushUniversal:
    def test_right_wins(self) -> None:
        assert smush_chars("X", "Y", 0, HARDBLANK) == "Y"

    def test_same_char(self) -> None:
        assert smush_chars("A", "A", 0, HARDBLANK) == "A"


# ---------------------------------------------------------------------------
# calc_smush_amount
# ---------------------------------------------------------------------------

class TestCalcSmushAmount:
    def test_fullwidth_returns_zero(self) -> None:
        assert calc_smush_amount("abc", "def", "fullwidth", 0, HARDBLANK) == 0

    def test_fitting_trailing_leading_spaces(self) -> None:
        # "abc   " has 3 trailing spaces, "   def" has 3 leading spaces -> 6
        result = calc_smush_amount("abc   ", "   def", "fitting", 0, HARDBLANK)
        assert result == 6

    def test_fitting_no_spaces(self) -> None:
        result = calc_smush_amount("abc", "def", "fitting", 0, HARDBLANK)
        assert result == 0

    def test_smushing_adds_one_when_smushable(self) -> None:
        # "abc " has 1 trailing space, " def" has 1 leading space -> 2 + 1 smush
        result = calc_smush_amount("abc ", " def", "smushing", 0, HARDBLANK)
        assert result == 3  # 1 trailing + 1 leading + 1 (universal smush)

    def test_smushing_no_extra_if_not_smushable(self) -> None:
        # Both hardblanks at boundary without hardblank rule -> no extra
        result = calc_smush_amount("ab$", "$cd", "smushing", SM_EQUAL, "$")
        assert result == 0  # no trailing/leading spaces, and hardblanks block

    def test_empty_lines(self) -> None:
        result = calc_smush_amount("", "abc", "smushing", 0, HARDBLANK)
        assert result == 0

    def test_all_spaces(self) -> None:
        result = calc_smush_amount("   ", "   ", "fitting", 0, HARDBLANK)
        assert result == 6
