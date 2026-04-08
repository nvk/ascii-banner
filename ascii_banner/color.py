# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""ANSI color support for ASCII art output."""

RESET = "\033[0m"

NAMED_COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

RAINBOW = [
    "\033[31m",  # red
    "\033[33m",  # yellow
    "\033[32m",  # green
    "\033[36m",  # cyan
    "\033[34m",  # blue
    "\033[35m",  # magenta
]


_COLOR_RGB = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "orange": (255, 128, 0),
    "pink": (255, 105, 180),
    "purple": (128, 0, 255),
}


def apply(text: str, color_name: str) -> str:
    """Apply color to text output."""
    color_name = color_name.strip()
    lower = color_name.lower()

    if lower == "rainbow":
        return _apply_rainbow(text)

    # Gradient: gradient:color1:color2
    if lower.startswith("gradient:"):
        parts = color_name.split(":")
        if len(parts) == 3:
            return _apply_gradient(text, parts[1], parts[2])
        if len(parts) == 2 and parts[1].lower() == "rainbow":
            return _apply_gradient_rainbow(text)
        return text

    # Named color
    if lower in NAMED_COLORS:
        return _apply_solid(text, NAMED_COLORS[lower])

    # Hex color (#rrggbb)
    if lower.startswith("#") and len(lower) == 7:
        try:
            r = int(lower[1:3], 16)
            g = int(lower[3:5], 16)
            b = int(lower[5:7], 16)
            code = f"\033[38;2;{r};{g};{b}m"
            return _apply_solid(text, code)
        except ValueError:
            pass

    return text


def _apply_solid(text: str, code: str) -> str:
    lines = text.split("\n")
    return "\n".join(code + line + RESET if line else line for line in lines)


def _apply_rainbow(text: str) -> str:
    lines = text.split("\n")
    result = []
    for line in lines:
        if not line:
            result.append(line)
            continue
        parts = []
        col_idx = 0
        for ch in line:
            if ch != " ":
                parts.append(RAINBOW[col_idx % len(RAINBOW)] + ch + RESET)
            else:
                parts.append(ch)
            col_idx += 1
        result.append("".join(parts))
    return "\n".join(result)


def _parse_color(name: str) -> tuple[int, int, int] | None:
    """Parse a color name or hex to RGB tuple."""
    name = name.lower().strip()
    if name in _COLOR_RGB:
        return _COLOR_RGB[name]
    if name.startswith("#") and len(name) == 7:
        try:
            return int(name[1:3], 16), int(name[3:5], 16), int(name[5:7], 16)
        except ValueError:
            pass
    return None


def _apply_gradient(text: str, start: str, end: str) -> str:
    """Apply a horizontal gradient between two colors."""
    c1 = _parse_color(start)
    c2 = _parse_color(end)
    if c1 is None or c2 is None:
        return text

    lines = text.split("\n")
    max_width = max((len(l) for l in lines), default=1)
    if max_width <= 1:
        max_width = 2

    result = []
    for line in lines:
        if not line:
            result.append(line)
            continue
        parts = []
        for i, ch in enumerate(line):
            if ch != " ":
                t = i / (max_width - 1)
                r = int(c1[0] + (c2[0] - c1[0]) * t)
                g = int(c1[1] + (c2[1] - c1[1]) * t)
                b = int(c1[2] + (c2[2] - c1[2]) * t)
                parts.append(f"\033[38;2;{r};{g};{b}m{ch}{RESET}")
            else:
                parts.append(ch)
        result.append("".join(parts))
    return "\n".join(result)


def _apply_gradient_rainbow(text: str) -> str:
    """Apply a smooth rainbow gradient across the full width."""
    import colorsys

    lines = text.split("\n")
    max_width = max((len(l) for l in lines), default=1)
    if max_width <= 1:
        max_width = 2

    result = []
    for line in lines:
        if not line:
            result.append(line)
            continue
        parts = []
        for i, ch in enumerate(line):
            if ch != " ":
                hue = i / max_width
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
                parts.append(f"\033[38;2;{ri};{gi};{bi}m{ch}{RESET}")
            else:
                parts.append(ch)
        result.append("".join(parts))
    return "\n".join(result)
