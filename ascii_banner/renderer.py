# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Render text as ASCII art using a FIGlet font."""

from __future__ import annotations

from .parser import Font
from .smushing import calc_smush_amount, smush_chars


def render(font: Font, text: str, width: int = 0, justify: str = "left") -> str:
    """Render text as ASCII art."""
    if not text:
        return ""

    mode = font.smush_mode
    rules = font.smush_rules
    height = font.height

    # Build output line by line
    output = [""] * height

    for ch in text:
        fig = font.get_char(ch)
        if fig.width == 0:
            continue

        # Calculate minimum smush amount across all rows
        smush_amt = fig.width
        for row in range(height):
            amt = calc_smush_amount(output[row], fig.lines[row], mode, rules, font.hardblank)
            if amt < smush_amt:
                smush_amt = amt

        # Merge character into output
        for row in range(height):
            output[row] = _smush_line(
                output[row], fig.lines[row], smush_amt, mode, rules, font.hardblank
            )

    # Trim trailing spaces
    max_width = 0
    for i, line in enumerate(output):
        output[i] = line.rstrip()
        if len(output[i]) > max_width:
            max_width = len(output[i])

    # Apply justification
    if width > 0 and justify != "left":
        for i, line in enumerate(output):
            if justify == "center":
                pad = (width - len(line)) // 2
                output[i] = " " * max(0, pad) + line
            elif justify == "right":
                pad = width - len(line)
                output[i] = " " * max(0, pad) + line

    return "\n".join(output)


def _smush_line(
    left: str, right: str, overlap: int, mode: str, rules: int, hardblank: str
) -> str:
    if not left:
        return right
    if overlap <= 0:
        return left + right

    left_len = len(left)
    right_len = len(right)

    parts = []

    # Part of left before overlap
    if left_len > overlap:
        parts.append(left[: left_len - overlap])

    # Overlap region
    overlap_start = max(0, left_len - overlap)
    for i in range(overlap):
        left_idx = overlap_start + i
        right_idx = i

        lchar = left[left_idx] if left_idx < left_len else " "
        rchar = right[right_idx] if right_idx < right_len else " "

        if mode == "smushing":
            smushed = smush_chars(lchar, rchar, rules, hardblank)
            if smushed is not None:
                parts.append(smushed)
                continue

        # Fitting: non-space wins
        parts.append(rchar if lchar == " " else lchar)

    # Rest of right after overlap
    if overlap < right_len:
        parts.append(right[overlap:])

    return "".join(parts)
