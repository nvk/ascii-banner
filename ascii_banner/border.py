# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Border/box wrapping for ASCII art output."""

from __future__ import annotations

STYLES: dict[str, dict[str, str]] = {
    "single": {"tl": "\u250c", "tr": "\u2510", "bl": "\u2514", "br": "\u2518",
               "h": "\u2500", "v": "\u2502"},
    "double": {"tl": "\u2554", "tr": "\u2557", "bl": "\u255a", "br": "\u255d",
               "h": "\u2550", "v": "\u2551"},
    "rounded": {"tl": "\u256d", "tr": "\u256e", "bl": "\u2570", "br": "\u256f",
                "h": "\u2500", "v": "\u2502"},
    "heavy": {"tl": "\u250f", "tr": "\u2513", "bl": "\u2517", "br": "\u251b",
              "h": "\u2501", "v": "\u2503"},
    "ascii": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
}


def wrap(text: str, style: str, padding: int = 1) -> str:
    """Wrap text in a border box."""
    style = style.lower().strip()
    s = STYLES.get(style)
    if s is None:
        return text

    lines = text.split("\n")
    max_width = max((len(line) for line in lines), default=0)
    pad = " " * padding
    inner_width = max_width + padding * 2

    result = []
    result.append(s["tl"] + s["h"] * inner_width + s["tr"])
    for line in lines:
        padded = line + " " * (max_width - len(line))
        result.append(s["v"] + pad + padded + pad + s["v"])
    result.append(s["bl"] + s["h"] * inner_width + s["br"])

    return "\n".join(result)


def list_styles() -> list[str]:
    """Return available border style names."""
    return sorted(STYLES.keys())
