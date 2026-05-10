# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Deterministic animation frame generation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .canvas import Canvas, Cell, RAINBOW_RGB, RGB


EFFECTS = (
    "reveal",
    "unfurl",
    "matrix",
    "print",
    "random",
    "decrypt",
    "wipe",
    "middleout",
    "slice",
    "slide",
    "scan",
    "colorshift",
    "glitch",
    "waves",
    "vhs",
    "rain",
    "sparkle",
    "fireworks",
    "laser",
    "errorcorrect",
    "pour",
    "burn",
    "smoke",
    "pipes",
    "starfield",
    "bubbles",
    "swarm",
    "blackhole",
    "synthgrid",
    "thunderstorm",
)

DIRECTIONS = ("left", "right", "up", "down")
BY_MODES = ("char", "line", "row", "column")
AXES = ("horizontal", "vertical", "both", "rows", "cols")
PALETTES = ("accent", "rainbow", "fire", "ocean")

_DEFAULT_DURATIONS = {
    "matrix": 2.5,
    "glitch": 2.0,
    "rain": 2.5,
    "fireworks": 2.5,
    "burn": 2.0,
    "smoke": 2.0,
    "starfield": 2.5,
    "swarm": 2.5,
    "blackhole": 2.5,
    "thunderstorm": 2.5,
}

_DEFAULT_DURATION = 1.5
_DEFAULT_GLYPHS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@#$%&*+-=?/"
_BINARY_GLYPHS = "01"
_HEX_GLYPHS = "0123456789ABCDEF"
_ASCII_GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_ACCENT_FALLBACK = (70, 255, 120)
_ORANGE = (255, 128, 0)
_WHITE = (255, 255, 255)


@dataclass(frozen=True)
class AnimationOptions:
    effect: str
    fps: int = 12
    duration: float | None = None
    loop: int = 1
    seed: int | None = None
    direction: str = "left"
    by: str = "char"
    axis: str = "both"
    charset: str | None = None
    intensity: float = 0.35
    palette: str = "accent"


@dataclass(frozen=True)
class Frame:
    canvas: Canvas
    delay_ms: int


def build_animation(final_canvas: Canvas, options: AnimationOptions) -> list[Frame]:
    """Build animation frames ending with the final canvas."""
    _validate_options(options)

    count = _frame_count(options)
    delay = max(1, int(round(1000 / options.fps)))

    if count <= 1 or final_canvas.width == 0 or final_canvas.height == 0:
        return [Frame(final_canvas, delay)]

    builders = {
        "reveal": lambda: _ordered_reveal(final_canvas, count, _reveal_order(final_canvas, options)),
        "unfurl": lambda: _wipe(final_canvas, count, options.direction),
        "matrix": lambda: _matrix(final_canvas, count, options),
        "print": lambda: _ordered_reveal(final_canvas, count, _print_order(final_canvas, options)),
        "random": lambda: _ordered_reveal(final_canvas, count, _random_order(final_canvas, options.seed)),
        "decrypt": lambda: _substitute(final_canvas, count, options, lock_start=0.15),
        "wipe": lambda: _wipe(final_canvas, count, options.direction),
        "middleout": lambda: _ordered_reveal(final_canvas, count, _middleout_order(final_canvas, options.axis)),
        "slice": lambda: _ordered_reveal(final_canvas, count, _slice_order(final_canvas, options)),
        "slide": lambda: _slide(final_canvas, count, options.direction),
        "scan": lambda: _scan(final_canvas, count, options),
        "colorshift": lambda: _colorshift(final_canvas, count, options),
        "glitch": lambda: _glitch(final_canvas, count, options),
        "waves": lambda: _waves(final_canvas, count, options),
        "vhs": lambda: _vhs(final_canvas, count, options),
        "rain": lambda: _rain(final_canvas, count, options),
        "sparkle": lambda: _sparkle(final_canvas, count, options),
        "fireworks": lambda: _fireworks(final_canvas, count, options),
        "laser": lambda: _laser(final_canvas, count, options),
        "errorcorrect": lambda: _substitute(final_canvas, count, options, lock_start=0.35),
        "pour": lambda: _pour(final_canvas, count, options),
        "burn": lambda: _burn(final_canvas, count, options),
        "smoke": lambda: _smoke(final_canvas, count, options),
        "pipes": lambda: _pipes(final_canvas, count, options),
        "starfield": lambda: _starfield(final_canvas, count, options),
        "bubbles": lambda: _bubbles(final_canvas, count, options),
        "swarm": lambda: _swarm(final_canvas, count, options),
        "blackhole": lambda: _blackhole(final_canvas, count, options),
        "synthgrid": lambda: _synthgrid(final_canvas, count, options),
        "thunderstorm": lambda: _thunderstorm(final_canvas, count, options),
    }
    canvases = builders[options.effect]()
    canvases[-1] = final_canvas
    return [Frame(canvas, delay) for canvas in canvases]


def _validate_options(options: AnimationOptions) -> None:
    if options.effect not in EFFECTS:
        raise ValueError(f"unknown animation effect: {options.effect}")
    if options.fps <= 0:
        raise ValueError("fps must be greater than zero")
    if options.duration is not None and options.duration <= 0:
        raise ValueError("duration must be greater than zero")
    if options.loop < 0:
        raise ValueError("loop must be zero or greater")
    if options.direction not in DIRECTIONS:
        raise ValueError(f"unknown animation direction: {options.direction}")
    if options.by not in BY_MODES:
        raise ValueError(f"unknown animation --by mode: {options.by}")
    if options.axis not in AXES:
        raise ValueError(f"unknown animation axis: {options.axis}")
    if not 0 <= options.intensity <= 1:
        raise ValueError("intensity must be between 0 and 1")
    if options.palette not in PALETTES:
        raise ValueError(f"unknown animation palette: {options.palette}")


def _frame_count(options: AnimationOptions) -> int:
    duration = options.duration
    if duration is None:
        duration = _DEFAULT_DURATIONS.get(options.effect, _DEFAULT_DURATION)
    return max(1, int(round(duration * options.fps)))


def _progress(index: int, count: int) -> float:
    return index / max(count - 1, 1)


def _blank_like(canvas: Canvas) -> Canvas:
    return Canvas.blank(canvas.width, canvas.height)


def _blank_grid(canvas: Canvas) -> list[list[Cell]]:
    return [[Cell(" ") for _x in range(canvas.width)] for _y in range(canvas.height)]


def _canvas_from_grid(grid: list[list[Cell]]) -> Canvas:
    height = len(grid)
    width = len(grid[0]) if grid else 0
    return Canvas(width, height, tuple(tuple(row) for row in grid))


def _set_cell(
    grid: list[list[Cell]],
    x: int,
    y: int,
    cell: Cell,
    *,
    overwrite: bool = False,
) -> None:
    if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
        if overwrite or grid[y][x].char == " ":
            grid[y][x] = cell


def _copy_positions(final_canvas: Canvas, positions: set[tuple[int, int]]) -> Canvas:
    def copy_cell(x: int, y: int, cell: Cell) -> Cell:
        if (x, y) in positions:
            return final_canvas.cells[y][x]
        return cell

    return _blank_like(final_canvas).map_cells(copy_cell)


def _visible_positions(canvas: Canvas) -> list[tuple[int, int]]:
    return [
        (x, y)
        for y, row in enumerate(canvas.cells)
        for x, cell in enumerate(row)
        if cell.char != " "
    ]


def _all_positions(canvas: Canvas) -> list[tuple[int, int]]:
    return [(x, y) for y in range(canvas.height) for x in range(canvas.width)]


def _ordered_reveal(final_canvas: Canvas, count: int, order: list[tuple[int, int]]) -> list[Canvas]:
    if not order:
        return [_blank_like(final_canvas) for _ in range(count - 1)] + [final_canvas]

    frames: list[Canvas] = []
    for index in range(count):
        shown = int(round(len(order) * _progress(index, count)))
        frames.append(_copy_positions(final_canvas, set(order[:shown])))
    return frames


def _reveal_order(final_canvas: Canvas, options: AnimationOptions) -> list[tuple[int, int]]:
    if options.by in ("line", "row"):
        return [
            pos
            for y in range(final_canvas.height)
            for pos in _visible_positions_in_row(final_canvas, y)
        ]
    if options.by == "column":
        return [
            pos
            for x in range(final_canvas.width)
            for pos in _visible_positions_in_col(final_canvas, x)
        ]
    return _visible_positions(final_canvas)


def _print_order(final_canvas: Canvas, options: AnimationOptions) -> list[tuple[int, int]]:
    return _reveal_order(final_canvas, options)


def _visible_positions_in_row(canvas: Canvas, y: int) -> list[tuple[int, int]]:
    return [(x, y) for x, cell in enumerate(canvas.cells[y]) if cell.char != " "]


def _visible_positions_in_col(canvas: Canvas, x: int) -> list[tuple[int, int]]:
    return [(x, y) for y in range(canvas.height) if canvas.cells[y][x].char != " "]


def _random_order(final_canvas: Canvas, seed: int | None) -> list[tuple[int, int]]:
    positions = _visible_positions(final_canvas)
    rng = random.Random(seed)
    rng.shuffle(positions)
    return positions


def _middleout_order(final_canvas: Canvas, axis: str) -> list[tuple[int, int]]:
    cx = (final_canvas.width - 1) / 2
    cy = (final_canvas.height - 1) / 2

    def distance(pos: tuple[int, int]) -> float:
        x, y = pos
        if axis == "horizontal":
            return abs(x - cx)
        if axis in ("vertical", "rows"):
            return abs(y - cy)
        return math.hypot(x - cx, y - cy)

    return sorted(_visible_positions(final_canvas), key=lambda pos: (distance(pos), pos[1], pos[0]))


def _slice_order(final_canvas: Canvas, options: AnimationOptions) -> list[tuple[int, int]]:
    axis = options.axis
    if axis in ("rows", "vertical"):
        rows = _outside_in_indices(final_canvas.height)
        return [pos for y in rows for pos in _visible_positions_in_row(final_canvas, y)]

    cols = _outside_in_indices(final_canvas.width)
    return [pos for x in cols for pos in _visible_positions_in_col(final_canvas, x)]


def _outside_in_indices(length: int) -> list[int]:
    order: list[int] = []
    left, right = 0, length - 1
    while left <= right:
        order.append(left)
        if right != left:
            order.append(right)
        left += 1
        right -= 1
    return order


def _wipe(final_canvas: Canvas, count: int, direction: str) -> list[Canvas]:
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        positions: set[tuple[int, int]] = set()
        if direction == "right":
            cutoff = final_canvas.width - int(round(final_canvas.width * p))
            positions = {(x, y) for y in range(final_canvas.height) for x in range(cutoff, final_canvas.width)}
        elif direction == "up":
            cutoff = final_canvas.height - int(round(final_canvas.height * p))
            positions = {(x, y) for y in range(cutoff, final_canvas.height) for x in range(final_canvas.width)}
        elif direction == "down":
            cutoff = int(round(final_canvas.height * p))
            positions = {(x, y) for y in range(cutoff) for x in range(final_canvas.width)}
        else:
            cutoff = int(round(final_canvas.width * p))
            positions = {(x, y) for y in range(final_canvas.height) for x in range(cutoff)}
        frames.append(_copy_positions(final_canvas, positions))
    return frames


def _slide(final_canvas: Canvas, count: int, direction: str) -> list[Canvas]:
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        if direction == "right":
            dx, dy = -round((1 - p) * final_canvas.width), 0
        elif direction == "up":
            dx, dy = 0, round((1 - p) * final_canvas.height)
        elif direction == "down":
            dx, dy = 0, -round((1 - p) * final_canvas.height)
        else:
            dx, dy = round((1 - p) * final_canvas.width), 0

        grid = _blank_grid(final_canvas)
        for y, row in enumerate(final_canvas.cells):
            for x, cell in enumerate(row):
                if cell.char != " ":
                    _set_cell(grid, x + dx, y + dy, cell, overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _substitute(
    final_canvas: Canvas,
    count: int,
    options: AnimationOptions,
    *,
    lock_start: float,
) -> list[Canvas]:
    rng = random.Random(options.seed)
    glyphs = _charset(options)
    accent = _accent_color(final_canvas)
    positions = _visible_positions(final_canvas)
    order = _random_order(final_canvas, options.seed)
    frames: list[Canvas] = []

    for index in range(count):
        p = _progress(index, count)
        lock_p = _scale_progress(p, lock_start, 1.0)
        locked = set(order[: int(len(order) * lock_p)])
        grid = _blank_grid(final_canvas)
        for x, y in positions:
            if (x, y) in locked:
                _set_cell(grid, x, y, final_canvas.cells[y][x], overwrite=True)
            else:
                _set_cell(grid, x, y, Cell(rng.choice(glyphs), fg=accent), overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _matrix(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    glyphs = _charset(options)
    accent = _accent_color(final_canvas)
    positions = _visible_positions(final_canvas)
    order = {pos: i for i, pos in enumerate(positions)}
    frames: list[Canvas] = []

    for index in range(count):
        p = _progress(index, count)
        lock_p = _scale_progress(p, 0.60, 1.0)
        locked_count = int(len(positions) * lock_p)
        grid = _blank_grid(final_canvas)

        for x in range(final_canvas.width):
            if rng.random() < 0.65:
                y = (index + x * 3 + rng.randrange(max(1, final_canvas.height))) % final_canvas.height
                _set_cell(grid, x, y, Cell(rng.choice(glyphs), fg=_dim(accent, 0.55)))

        for y, row in enumerate(final_canvas.cells):
            for x, cell in enumerate(row):
                pos = (x, y)
                if cell.char == " ":
                    continue
                if order[pos] < locked_count:
                    _set_cell(grid, x, y, cell, overwrite=True)
                elif rng.random() < 0.70:
                    _set_cell(grid, x, y, Cell(rng.choice(glyphs), fg=accent), overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _scan(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    frames: list[Canvas] = []
    width = max(2, final_canvas.width // 8)
    for index in range(count):
        p = _progress(index, count)
        band = round((final_canvas.width + width * 2) * p) - width
        frames.append(
            final_canvas.map_cells(
                lambda x, _y, cell: _highlight(cell, accent)
                if cell.char != " " and abs(x - band) <= width
                else cell
            )
        )
    return frames


def _colorshift(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        frames.append(
            final_canvas.map_cells(
                lambda x, y, cell: cell.with_fg(
                    _palette_color(options.palette, accent, x, y, index, count)
                )
                if cell.char != " "
                else cell
            )
        )
    return frames


def _glitch(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    glyphs = _charset(options)
    accent = _accent_color(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        chance = options.intensity * (1 - p)
        grid = _blank_grid(final_canvas)
        for y, row in enumerate(final_canvas.cells):
            row_shift = rng.choice((-1, 0, 0, 1)) if rng.random() < chance else 0
            for x, cell in enumerate(row):
                if cell.char == " ":
                    continue
                if rng.random() < chance:
                    out = Cell(rng.choice(glyphs), fg=accent)
                elif rng.random() < chance / 2:
                    continue
                else:
                    out = cell
                _set_cell(grid, x + row_shift, y, out, overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _waves(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        phase = 2 * math.pi * _progress(index, count)
        frames.append(
            final_canvas.map_cells(
                lambda x, y, cell: cell.with_fg(
                    _blend(cell.fg or accent, _WHITE, (math.sin(x * 0.55 + y + phase) + 1) * 0.25)
                )
                if cell.char != " "
                else cell
            )
        )
    return frames


def _vhs(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        chance = options.intensity * (1 - p)
        grid = _blank_grid(final_canvas)
        for y, row in enumerate(final_canvas.cells):
            shift = rng.choice((-2, -1, 0, 0, 1, 2)) if rng.random() < chance else 0
            for x, cell in enumerate(row):
                if cell.char == " " or rng.random() < chance * 0.25:
                    continue
                out = cell.with_fg(_dim(cell.fg or accent, 0.65)) if rng.random() < chance else cell
                _set_cell(grid, x + shift, y, out, overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _rain(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    positions = _random_order(final_canvas, options.seed)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = _copy_positions(final_canvas, set(positions[: int(len(positions) * p)])).cells
        mutable = [list(row) for row in grid]
        for x in range(final_canvas.width):
            for offset in (0, final_canvas.height // 2 + 1):
                y = (index + x * 5 + offset) % max(1, final_canvas.height)
                _set_cell(mutable, x, y, Cell("|", fg=_dim(accent, 0.55)))
        frames.append(_canvas_from_grid(mutable))
    return frames


def _sparkle(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    positions = _visible_positions(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in final_canvas.cells]
        sparkle_count = max(1, int(len(positions) * options.intensity * (1 - p)))
        for x, y in rng.sample(positions, min(len(positions), sparkle_count)):
            _set_cell(grid, x, y, Cell(rng.choice("*+."), fg=_highlight_color(accent)), overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _fireworks(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    centers = [
        (rng.randrange(max(1, final_canvas.width)), rng.randrange(max(1, final_canvas.height)))
        for _ in range(max(2, min(6, final_canvas.width // 8 + 1)))
    ]
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in final_canvas.cells]
        for cx, cy in centers:
            radius = int((1 + final_canvas.width // 5) * ((p * 2) % 1))
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x = cx + round(math.cos(rad) * radius)
                y = cy + round(math.sin(rad) * radius * 0.55)
                _set_cell(grid, x, y, Cell("*" if radius % 2 else "+", fg=accent), overwrite=False)
        frames.append(_canvas_from_grid(grid))
    return frames


def _laser(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    order = _visible_positions(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in _copy_positions(final_canvas, set(order[: int(len(order) * p)])).cells]
        beam_x = min(final_canvas.width - 1, round(final_canvas.width * p))
        for y in range(final_canvas.height):
            _set_cell(grid, beam_x, y, Cell("|", fg=_highlight_color(accent)), overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _pour(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    starts = {
        pos: -1 - rng.randrange(max(1, final_canvas.height))
        for pos in _visible_positions(final_canvas)
    }
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = _blank_grid(final_canvas)
        for (x, y), start_y in starts.items():
            cur_y = round(start_y + (y - start_y) * p)
            _set_cell(grid, x, cur_y, final_canvas.cells[y][x], overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _burn(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas, fallback=_ORANGE)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        cutoff = final_canvas.height - round(final_canvas.height * p)
        grid = _blank_grid(final_canvas)
        for y in range(cutoff, final_canvas.height):
            for x, cell in enumerate(final_canvas.cells[y]):
                if cell.char != " ":
                    _set_cell(grid, x, y, cell, overwrite=True)
        flame_y = max(0, cutoff - 1)
        for x in range(final_canvas.width):
            if rng.random() < 0.35:
                _set_cell(grid, x, flame_y, Cell(rng.choice(".:^*#"), fg=accent), overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _smoke(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    order = _middleout_order(final_canvas, "both")
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in _copy_positions(final_canvas, set(order[: int(len(order) * p)])).cells]
        smoke_count = max(1, int(final_canvas.width * final_canvas.height * options.intensity * (1 - p)))
        for _ in range(smoke_count):
            x = rng.randrange(max(1, final_canvas.width))
            y = rng.randrange(max(1, final_canvas.height))
            _set_cell(grid, x, y, Cell(rng.choice(".,:~"), fg=_dim(accent, 0.45)), overwrite=False)
        frames.append(_canvas_from_grid(grid))
    return frames


def _pipes(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    path = _pipe_path(final_canvas)
    reveal_order = _visible_positions(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in _copy_positions(final_canvas, set(reveal_order[: int(len(reveal_order) * p)])).cells]
        pipe_count = int(len(path) * p)
        for x, y, ch in path[:pipe_count]:
            _set_cell(grid, x, y, Cell(ch, fg=accent), overwrite=False)
        frames.append(_canvas_from_grid(grid))
    return frames


def _pipe_path(canvas: Canvas) -> list[tuple[int, int, str]]:
    if canvas.width == 0 or canvas.height == 0:
        return []
    path: list[tuple[int, int, str]] = []
    for x in range(canvas.width):
        path.append((x, 0, "-"))
    for y in range(1, canvas.height):
        path.append((canvas.width - 1, y, "|"))
    if canvas.height > 1:
        for x in range(canvas.width - 2, -1, -1):
            path.append((x, canvas.height - 1, "-"))
    for y in range(canvas.height - 2, 0, -1):
        path.append((0, y, "|"))
    return path


def _starfield(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    stars = [
        (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.1, 1.0))
        for _ in range(max(12, final_canvas.width))
    ]
    order = _visible_positions(final_canvas)
    cx, cy = final_canvas.width / 2, final_canvas.height / 2
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in _copy_positions(final_canvas, set(order[: int(len(order) * p)])).cells]
        for sx, sy, depth in stars:
            scale = 1 + ((p + depth) % 1) * 2.5
            x = round(cx + sx * cx * scale)
            y = round(cy + sy * cy * scale)
            _set_cell(grid, x, y, Cell("." if scale < 2 else "*", fg=_dim(accent, 0.65)), overwrite=False)
        frames.append(_canvas_from_grid(grid))
    return frames


def _bubbles(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    accent = _accent_color(final_canvas)
    bubbles = [
        (rng.randrange(max(1, final_canvas.width)), rng.randrange(max(1, final_canvas.height)))
        for _ in range(max(4, final_canvas.width // 3))
    ]
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in final_canvas.cells]
        for x, start_y in bubbles:
            y = (start_y - index) % max(1, final_canvas.height)
            _set_cell(grid, x, y, Cell("o" if (index + x) % 2 else "O", fg=_dim(accent, 0.75)), overwrite=False)
        if p < 1:
            frames.append(_canvas_from_grid(grid))
    frames.append(final_canvas)
    return frames[:count]


def _swarm(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    rng = random.Random(options.seed)
    starts = {
        pos: (rng.randrange(max(1, final_canvas.width)), rng.randrange(max(1, final_canvas.height)))
        for pos in _visible_positions(final_canvas)
    }
    return _trajectory(final_canvas, count, starts)


def _blackhole(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    cx = (final_canvas.width - 1) / 2
    cy = (final_canvas.height - 1) / 2
    starts: dict[tuple[int, int], tuple[int, int]] = {}
    for x, y in _visible_positions(final_canvas):
        angle = math.atan2(y - cy, x - cx) + math.pi / 2
        radius = 1 + ((x + y) % max(2, final_canvas.width // 2 + 1))
        starts[(x, y)] = (round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius * 0.5))
    return _trajectory(final_canvas, count, starts)


def _trajectory(
    final_canvas: Canvas,
    count: int,
    starts: dict[tuple[int, int], tuple[int, int]],
) -> list[Canvas]:
    frames: list[Canvas] = []
    for index in range(count):
        p = _ease_out(_progress(index, count))
        grid = _blank_grid(final_canvas)
        for (x, y), (sx, sy) in starts.items():
            cur_x = round(sx + (x - sx) * p)
            cur_y = round(sy + (y - sy) * p)
            _set_cell(grid, cur_x, cur_y, final_canvas.cells[y][x], overwrite=True)
        frames.append(_canvas_from_grid(grid))
    return frames


def _synthgrid(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    order = _visible_positions(final_canvas)
    frames: list[Canvas] = []
    for index in range(count):
        p = _progress(index, count)
        grid = [list(row) for row in _copy_positions(final_canvas, set(order[: int(len(order) * p)])).cells]
        for y in range(final_canvas.height):
            if (y + index) % 3 == 0:
                for x in range(final_canvas.width):
                    _set_cell(grid, x, y, Cell("-", fg=_dim(accent, 0.35)), overwrite=False)
        center = final_canvas.width // 2
        for offset in range(0, max(1, final_canvas.width), max(2, final_canvas.width // 8)):
            for y in range(final_canvas.height):
                spread = round(offset * (y + 1) / max(1, final_canvas.height))
                _set_cell(grid, center - spread, y, Cell("/", fg=_dim(accent, 0.35)), overwrite=False)
                _set_cell(grid, center + spread, y, Cell("\\", fg=_dim(accent, 0.35)), overwrite=False)
        frames.append(_canvas_from_grid(grid))
    return frames


def _thunderstorm(final_canvas: Canvas, count: int, options: AnimationOptions) -> list[Canvas]:
    accent = _accent_color(final_canvas)
    frames = _rain(final_canvas, count, options)
    out: list[Canvas] = []
    for index, canvas in enumerate(frames):
        grid = [list(row) for row in canvas.cells]
        if index % max(2, count // 4) == 0:
            x = (index * 7) % max(1, final_canvas.width)
            for y in range(final_canvas.height):
                _set_cell(grid, x + (y % 3) - 1, y, Cell("/", fg=_highlight_color(accent)), overwrite=True)
        out.append(_canvas_from_grid(grid))
    return out


def _scale_progress(value: float, start: float, end: float) -> float:
    if value <= start:
        return 0.0
    if value >= end:
        return 1.0
    return (value - start) / (end - start)


def _ease_out(value: float) -> float:
    return 1 - (1 - value) * (1 - value)


def _charset(options: AnimationOptions) -> str:
    if not options.charset:
        return _DEFAULT_GLYPHS
    lower = options.charset.lower()
    if lower == "binary":
        return _BINARY_GLYPHS
    if lower == "hex":
        return _HEX_GLYPHS
    if lower == "ascii":
        return _ASCII_GLYPHS
    return options.charset or _DEFAULT_GLYPHS


def _accent_color(canvas: Canvas, fallback: RGB = _ACCENT_FALLBACK) -> RGB:
    colors = [
        cell.fg
        for row in canvas.cells
        for cell in row
        if cell.char != " " and cell.fg is not None
    ]
    if not colors:
        return fallback
    return (
        round(sum(color[0] for color in colors) / len(colors)),
        round(sum(color[1] for color in colors) / len(colors)),
        round(sum(color[2] for color in colors) / len(colors)),
    )


def _palette_color(
    palette: str,
    accent: RGB,
    x: int,
    y: int,
    index: int,
    count: int,
) -> RGB:
    if palette == "rainbow":
        return RAINBOW_RGB[(x + y + index) % len(RAINBOW_RGB)]
    if palette == "fire":
        colors = (_ORANGE, (255, 220, 80), (255, 64, 0))
        return colors[(x + index) % len(colors)]
    if palette == "ocean":
        colors = ((0, 180, 255), (0, 255, 180), (50, 100, 255))
        return colors[(x + y + index) % len(colors)]
    pulse = (math.sin(2 * math.pi * (index / max(1, count - 1)) + x * 0.25) + 1) / 2
    return _blend(_dim(accent, 0.55), _WHITE, pulse * 0.35)


def _highlight(cell: Cell, accent: RGB) -> Cell:
    return cell.with_fg(_highlight_color(cell.fg or accent))


def _highlight_color(rgb: RGB) -> RGB:
    return _blend(rgb, _WHITE, 0.45)


def _blend(a: RGB, b: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


def _dim(rgb: RGB, factor: float) -> RGB:
    return (
        max(0, min(255, round(rgb[0] * factor))),
        max(0, min(255, round(rgb[1] * factor))),
        max(0, min(255, round(rgb[2] * factor))),
    )
