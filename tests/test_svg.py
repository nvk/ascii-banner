# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.svg — vector SVG rendering."""

import pytest

from ascii_banner import svg
from ascii_banner.parser import load
from ascii_banner.renderer import render


# ---------------------------------------------------------------------------
# Glyph table — per-character rect counts
# ---------------------------------------------------------------------------

class TestGlyphTable:
    def test_default_block_is_full_cell(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20, mode="default")
        assert t["█"] == [(0, 0, 100, 200)]

    def test_inset_block_shrinks(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20, mode="inset")
        (x, y, w, h) = t["█"][0]
        assert (x, y) == (0, 0)
        assert w < 100 and h < 200

    def test_extend_block_overflows(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20, mode="extend")
        (x, y, w, h) = t["█"][0]
        assert (x, y) == (0, 0)
        assert w > 100 and h > 200

    def test_double_lines_are_two_rects(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20)
        assert len(t["║"]) == 2
        assert len(t["═"]) == 2

    def test_corners_are_four_rects(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20)
        for corner in "╔╗╚╝":
            assert len(t[corner]) == 4, f"{corner} should be 4 rects"

    def test_space_is_empty(self) -> None:
        t = svg.build_glyph_table(100, 200, 15, 20)
        assert t[" "] == []

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError):
            svg.build_glyph_table(100, 200, 15, 20, mode="bogus")


# ---------------------------------------------------------------------------
# Banner walking + error reporting
# ---------------------------------------------------------------------------

class TestBannerToRects:
    def test_unsupported_glyph_raises(self) -> None:
        glyphs = svg.build_glyph_table(100, 200, 15, 20)
        with pytest.raises(svg.UnsupportedGlyphError) as exc:
            svg.banner_to_rects("XYZ", glyphs, 100, 200)
        assert "U+0058" in str(exc.value)

    def test_empty_banner_zero_rects(self) -> None:
        glyphs = svg.build_glyph_table(100, 200, 15, 20)
        assert svg.banner_to_rects("", glyphs, 100, 200) == []

    def test_only_spaces_zero_rects(self) -> None:
        glyphs = svg.build_glyph_table(100, 200, 15, 20)
        assert svg.banner_to_rects("    ", glyphs, 100, 200) == []


# ---------------------------------------------------------------------------
# Merge — adjacency only, must preserve fill
# ---------------------------------------------------------------------------

class TestMerge:
    def test_horizontal_run_collapses(self) -> None:
        # Four 10×5 rects laid end to end at y=0 should merge to one 40×5.
        rects = [(0, 0, 10, 5), (10, 0, 10, 5), (20, 0, 10, 5), (30, 0, 10, 5)]
        merged = svg.merge_rects(rects)
        assert merged == [(0, 0, 40, 5)]

    def test_non_adjacent_does_not_merge(self) -> None:
        rects = [(0, 0, 10, 5), (20, 0, 10, 5)]
        merged = svg.merge_rects(rects)
        assert sorted(merged) == sorted(rects)

    def test_merge_reduces_real_banner(self) -> None:
        font = load("ANSI Shadow")
        banner = render(font, "LLM WIKI")
        raw = svg.to_svg(banner, merge=False)
        compact = svg.to_svg(banner, merge=True)
        # Same render area, fewer rect tags.
        assert raw.count("<rect") > compact.count("<rect")


# ---------------------------------------------------------------------------
# End-to-end via figlet
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_ansi_shadow_round_trip(self) -> None:
        font = load("ANSI Shadow")
        banner = render(font, "LLM WIKI")
        doc = svg.to_svg(banner)
        assert doc.startswith("<?xml")
        assert "<svg " in doc
        assert "</svg>" in doc
        assert "<rect" in doc

    def test_modes_produce_distinct_output(self) -> None:
        font = load("ANSI Shadow")
        banner = render(font, "LL")
        a = svg.to_svg(banner, mode="default")
        b = svg.to_svg(banner, mode="inset")
        c = svg.to_svg(banner, mode="extend")
        assert a != b != c != a
