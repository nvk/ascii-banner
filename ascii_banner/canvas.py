# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""ANSI-free cell canvas used by animations and media export."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Callable


RGB = tuple[int, int, int]


NAMED_RGB: dict[str, RGB] = {
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "blue": (0, 0, 255),
    "magenta": (255, 0, 255),
    "cyan": (0, 255, 255),
    "white": (255, 255, 255),
    "orange": (255, 128, 0),
    "pink": (255, 105, 180),
    "purple": (128, 0, 255),
}


RAINBOW_RGB: tuple[RGB, ...] = (
    (255, 0, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 255),
    (0, 0, 255),
    (255, 0, 255),
)


@dataclass(frozen=True)
class Cell:
    """One monospaced display cell."""

    char: str = " "
    fg: RGB | None = None
    bg: RGB | None = None
    bold: bool = False

    def __post_init__(self) -> None:
        if len(self.char) != 1:
            raise ValueError("cell char must be exactly one codepoint")

    def with_char(self, char: str) -> "Cell":
        return Cell(char, fg=self.fg, bg=self.bg, bold=self.bold)

    def with_fg(self, fg: RGB | None) -> "Cell":
        return Cell(self.char, fg=fg, bg=self.bg, bold=self.bold)


@dataclass(frozen=True)
class Canvas:
    """Fixed-size grid of monospaced cells."""

    width: int
    height: int
    cells: tuple[tuple[Cell, ...], ...]

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("canvas dimensions must be non-negative")
        if len(self.cells) != self.height:
            raise ValueError("canvas row count does not match height")
        for row in self.cells:
            if len(row) != self.width:
                raise ValueError("canvas row width does not match width")

    @classmethod
    def blank(
        cls,
        width: int,
        height: int,
        *,
        fill: str = " ",
        fg: RGB | None = None,
        bg: RGB | None = None,
    ) -> "Canvas":
        cell = Cell(fill, fg=fg, bg=bg)
        rows = tuple(tuple(cell for _ in range(width)) for _ in range(height))
        return cls(width, height, rows)

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        fg: RGB | None = None,
        bg: RGB | None = None,
    ) -> "Canvas":
        if text == "":
            return cls.blank(0, 0)

        lines = text.split("\n")
        width = max((len(line) for line in lines), default=0)
        rows: list[tuple[Cell, ...]] = []
        for line in lines:
            row = [Cell(ch, fg=fg, bg=bg) for ch in line]
            row.extend(Cell(" ", fg=fg, bg=bg) for _ in range(width - len(row)))
            rows.append(tuple(row))
        return cls(width, len(rows), tuple(rows))

    def map_cells(self, func: Callable[[int, int, Cell], Cell]) -> "Canvas":
        rows = []
        for y, row in enumerate(self.cells):
            rows.append(tuple(func(x, y, cell) for x, cell in enumerate(row)))
        return Canvas(self.width, self.height, tuple(rows))

    def to_lines(self, *, trim: bool = False) -> list[str]:
        lines = ["".join(cell.char for cell in row) for row in self.cells]
        if trim:
            return [line.rstrip() for line in lines]
        return lines

    def to_text(self, *, trim: bool = False) -> str:
        return "\n".join(self.to_lines(trim=trim))

    def has_style(self) -> bool:
        return any(
            cell.fg is not None or cell.bg is not None or cell.bold
            for row in self.cells
            for cell in row
        )


def parse_rgb(value: str) -> RGB | None:
    """Parse a named color or #rrggbb value."""
    lower = value.strip().lower()
    if lower in NAMED_RGB:
        return NAMED_RGB[lower]
    if lower.startswith("#") and len(lower) == 7:
        try:
            return (
                int(lower[1:3], 16),
                int(lower[3:5], 16),
                int(lower[5:7], 16),
            )
        except ValueError:
            return None
    return None


def apply_color(canvas: Canvas, color_spec: str) -> Canvas:
    """Apply a color spec to visible cells without inserting ANSI codes."""
    spec = color_spec.strip()
    lower = spec.lower()

    if lower == "rainbow":
        return _apply_rainbow(canvas)

    if lower.startswith("gradient:"):
        parts = spec.split(":")
        if len(parts) == 2 and parts[1].lower() == "rainbow":
            return _apply_gradient_rainbow(canvas)
        if len(parts) == 3:
            start = parse_rgb(parts[1])
            end = parse_rgb(parts[2])
            if start is not None and end is not None:
                return _apply_gradient(canvas, start, end)
        return canvas

    rgb = parse_rgb(spec)
    if rgb is None:
        return canvas
    return _apply_solid(canvas, rgb)


def _visible(cell: Cell) -> bool:
    return cell.char != " "


def _apply_solid(canvas: Canvas, rgb: RGB) -> Canvas:
    return canvas.map_cells(
        lambda _x, _y, cell: cell.with_fg(rgb) if _visible(cell) else cell
    )


def _apply_rainbow(canvas: Canvas) -> Canvas:
    def color_cell(x: int, _y: int, cell: Cell) -> Cell:
        if not _visible(cell):
            return cell
        return cell.with_fg(RAINBOW_RGB[x % len(RAINBOW_RGB)])

    return canvas.map_cells(color_cell)


def _apply_gradient(canvas: Canvas, start: RGB, end: RGB) -> Canvas:
    denom = max(canvas.width - 1, 1)

    def color_cell(x: int, _y: int, cell: Cell) -> Cell:
        if not _visible(cell):
            return cell
        t = x / denom
        return cell.with_fg(
            (
                int(start[0] + (end[0] - start[0]) * t),
                int(start[1] + (end[1] - start[1]) * t),
                int(start[2] + (end[2] - start[2]) * t),
            )
        )

    return canvas.map_cells(color_cell)


def _apply_gradient_rainbow(canvas: Canvas) -> Canvas:
    denom = max(canvas.width, 1)

    def color_cell(x: int, _y: int, cell: Cell) -> Cell:
        if not _visible(cell):
            return cell
        r, g, b = colorsys.hsv_to_rgb(x / denom, 1.0, 1.0)
        return cell.with_fg((int(r * 255), int(g * 255), int(b * 255)))

    return canvas.map_cells(color_cell)
