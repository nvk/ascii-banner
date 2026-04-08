# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""FIGlet horizontal smushing rules."""

# Smushing rule flags
SM_EQUAL = 1      # Rule 1: Equal character
SM_LOWLINE = 2    # Rule 2: Underscore
SM_HIERARCHY = 4  # Rule 3: Hierarchy
SM_PAIR = 8       # Rule 4: Opposite pair
SM_BIGX = 16      # Rule 5: Big X
SM_HARDBLANK = 32 # Rule 6: Hardblank

_REPLACE_CHARS = set("|/\\[]{}()<>")

_PAIRS = [
    ("[", "]"), ("]", "["),
    ("{", "}"), ("}", "{"),
    ("(", ")"), (")", "("),
]


def smush_chars(left: str, right: str, rules: int, hardblank: str) -> str | None:
    """Attempt to smush two characters. Returns the result or None."""
    if left == " ":
        return right
    if right == " ":
        return left

    # Both hardblanks
    if left == hardblank and right == hardblank:
        if rules & SM_HARDBLANK:
            return left
        return None

    # One hardblank
    if left == hardblank or right == hardblank:
        return None

    # Universal smushing (no rules) — right wins
    if rules == 0:
        return right

    # Rule 1: Equal character
    if rules & SM_EQUAL and left == right:
        return left

    # Rule 2: Underscore
    if rules & SM_LOWLINE:
        if left == "_" and right in _REPLACE_CHARS:
            return right
        if right == "_" and left in _REPLACE_CHARS:
            return left

    # Rule 3: Hierarchy
    if rules & SM_HIERARCHY:
        lc = _hier_class(left)
        rc = _hier_class(right)
        if lc > 0 and rc > 0 and lc != rc:
            return left if lc > rc else right

    # Rule 4: Opposite pair
    if rules & SM_PAIR:
        for a, b in _PAIRS:
            if left == a and right == b:
                return "|"

    # Rule 5: Big X
    if rules & SM_BIGX:
        if left == "/" and right == "\\":
            return "|"
        if left == "\\" and right == "/":
            return "Y"
        if left == ">" and right == "<":
            return "X"

    return None


def calc_smush_amount(
    left_line: str, right_line: str, mode: str, rules: int, hardblank: str
) -> int:
    """Calculate how many columns the right can overlap onto the left."""
    if mode == "fullwidth":
        return 0

    # Trailing spaces on left
    left_trimmed = left_line.rstrip(" ")
    trailing = len(left_line) - len(left_trimmed)

    # Leading spaces on right
    right_trimmed = right_line.lstrip(" ")
    leading = len(right_line) - len(right_trimmed)

    amount = trailing + leading

    if mode == "smushing" and left_trimmed and right_trimmed:
        lchar = left_trimmed[-1]
        rchar = right_trimmed[0]
        if smush_chars(lchar, rchar, rules, hardblank) is not None:
            amount += 1

    return amount


def _hier_class(ch: str) -> int:
    if ch == "|":
        return 1
    if ch in ("/", "\\"):
        return 2
    if ch in ("[", "]"):
        return 3
    if ch in ("{", "}"):
        return 4
    if ch in ("(", ")"):
        return 5
    if ch in ("<", ">"):
        return 6
    return 0
