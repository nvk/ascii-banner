# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Pure-vector SVG rendering of ASCII-art banners.

Each Unicode box-drawing/block glyph maps to one or more cell-local
rectangles. No font dependency, no rasterization — output is geometric
SVG suitable for vinyl plotters, laser cutters, or print at any scale.

Currently covers the 7 glyphs used by the figlet ANSI Shadow font
(U+2588 plus the six double-line box-drawing characters). Other fonts
that use unsupported glyphs raise UnsupportedGlyphError.
"""

from __future__ import annotations

from typing import Iterable


class UnsupportedGlyphError(ValueError):
    """Raised when the ASCII art contains a glyph the renderer can't draw."""


# Block characters mapped to cell-local (x, y, w, h) rectangles.
# Geometry is parameterized on cell size W,H, stroke S, gap G — see
# build_glyph_table() for the canonical placement.

Rect = tuple[float, float, float, float]


def build_glyph_table(W: float, H: float, S: float, G: float,
                      mode: str = "default") -> dict[str, list[Rect]]:
    """Return {char: list of cell-local rects} for the supported glyphs.

    XL/XR are the left edges of the left/right vertical line of a double.
    YT/YB are the top edges of the top/bottom horizontal line of a double.
    The double stroke band (total width 2S+G) is centered in the cell.

    Mode controls only the █ FULL BLOCK rendering:
      default — block fills its cell. Authentic ANSI-Shadow look with a
                visible step where a block meets a centered corner glyph.
      inset   — block shrinks to (W-XL)×(H-YT). Letters look lighter and
                gain visible inter-cell gaps (8-bit / glitch aesthetic).
      extend  — block grows to (W+XL)×(H+YT), overflowing into the
                adjacent shadow cell's empty band so the front face stays
                solid and the shadow attaches as a continuous outline.
                Best for sticker production. Safe because every █ in
                supported figlet output is followed by a shadow glyph
                (never by raw whitespace).
    """
    XL = (W - 2 * S - G) / 2
    XR = XL + S + G
    YT = (H - 2 * S - G) / 2
    YB = YT + S + G

    if mode == "default":
        block: list[Rect] = [(0, 0, W, H)]
    elif mode == "inset":
        block = [(0, 0, W - XL, H - YT)]
    elif mode == "extend":
        block = [(0, 0, W + XL, H + YT)]
    else:
        raise ValueError(f"unknown mode: {mode!r}")

    return {
        " ": [],
        "█": block,
        "║": [(XL, 0, S, H), (XR, 0, S, H)],
        "═": [(0, YT, W, S), (0, YB, W, S)],
        # ╔ DOUBLE DOWN AND RIGHT — outer corner top-left
        "╔": [
            (XL, YT, W - XL, S),
            (XL, YT, S, H - YT),
            (XR, YB, W - XR, S),
            (XR, YB, S, H - YB),
        ],
        # ╗ DOUBLE DOWN AND LEFT — outer corner top-right
        "╗": [
            (0, YT, XR + S, S),
            (XR, YT, S, H - YT),
            (0, YB, XL + S, S),
            (XL, YB, S, H - YB),
        ],
        # ╚ DOUBLE UP AND RIGHT — outer corner bottom-left
        "╚": [
            (XL, YB, W - XL, S),
            (XL, 0, S, YB + S),
            (XR, YT, W - XR, S),
            (XR, 0, S, YT + S),
        ],
        # ╝ DOUBLE UP AND LEFT — outer corner bottom-right
        "╝": [
            (0, YB, XR + S, S),
            (XR, 0, S, YB + S),
            (0, YT, XL + S, S),
            (XL, 0, S, YT + S),
        ],
    }


def banner_to_rects(banner: str, glyphs: dict[str, list[Rect]],
                    W: float, H: float) -> list[Rect]:
    """Walk every cell of the banner, emit absolute-positioned rects."""
    rects: list[Rect] = []
    for row, line in enumerate(banner.split("\n")):
        for col, ch in enumerate(line):
            if ch not in glyphs:
                raise UnsupportedGlyphError(
                    f"glyph {ch!r} (U+{ord(ch):04X}) at row {row}, col {col} "
                    f"is not supported by the SVG renderer"
                )
            for (rx, ry, rw, rh) in glyphs[ch]:
                rects.append((col * W + rx, row * H + ry, rw, rh))
    return rects


def merge_rects(rects: Iterable[Rect]) -> list[Rect]:
    """Two-pass adjacency merge (horizontal then vertical).

    Collapses runs of cell-aligned rects with matching y/height into a single
    wider rect, then stacks rects with matching x/width into taller rects.
    Pure adjacency only — does not union arbitrary overlaps. Cuts SVG size
    dramatically without changing the rendered shape.
    """
    def pass_merge(items: list[Rect], key_idx: int, span_idx: int,
                   var_idx: int, len_idx: int) -> list[Rect]:
        groups: dict[tuple[float, float], list[tuple[float, float]]] = {}
        for r in items:
            groups.setdefault((r[key_idx], r[span_idx]), []).append(
                (r[var_idx], r[len_idx])
            )
        out: list[tuple[float, float, float, float]] = []
        for (k, s), runs in groups.items():
            runs.sort()
            cur_v, cur_l = runs[0]
            for v, l in runs[1:]:
                if v <= cur_v + cur_l + 1e-9:
                    cur_l = max(cur_v + cur_l, v + l) - cur_v
                else:
                    out.append((cur_v, cur_l, k, s))
                    cur_v, cur_l = v, l
            out.append((cur_v, cur_l, k, s))
        if key_idx == 1:
            return [(v, k, l, s) for (v, l, k, s) in out]
        return [(k, v, s, l) for (v, l, k, s) in out]

    merged = pass_merge(list(rects), 1, 3, 0, 2)
    merged = pass_merge(merged,      0, 2, 1, 3)
    return merged


def render_svg(rects: Iterable[Rect], cols: int, rows: int,
               W: float, H: float, fill: str, bg: str) -> str:
    width = cols * W
    height = rows * H
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width:g} {height:g}" '
        f'width="{width:g}" height="{height:g}" '
        f'shape-rendering="crispEdges">',
    ]
    if bg:
        out.append(f'<rect width="{width:g}" height="{height:g}" fill="{bg}"/>')
    out.append(f'<g fill="{fill}">')
    for (x, y, w, h) in rects:
        out.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/>')
    out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def to_svg(banner: str, *,
           cell_width: float = 100,
           cell_height: float = 200,
           stroke: float = 15,
           gap: float = 20,
           mode: str = "extend",
           merge: bool = False,
           fill: str = "#000",
           bg: str = "") -> str:
    """Render an ASCII-art banner string to a self-contained SVG document.

    The banner is interpreted as a grid of monospaced cells of size
    cell_width × cell_height. Defaults match a typical 1:2 terminal cell.
    The default mode is `extend` — empirically the cleanest output for
    sticker / cutter use (front face stays solid, shadow is continuous).
    """
    banner = banner.rstrip("\n")
    glyphs = build_glyph_table(cell_width, cell_height, stroke, gap, mode=mode)
    rects = banner_to_rects(banner, glyphs, cell_width, cell_height)
    if merge:
        rects = merge_rects(rects)
    lines = banner.split("\n")
    cols = max((len(line) for line in lines), default=0)
    rows = len(lines)
    return render_svg(rects, cols, rows, cell_width, cell_height, fill, bg)


SUPPORTED_GLYPHS = frozenset(" █║═╔╗╚╝")

