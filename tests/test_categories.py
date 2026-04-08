# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.categories — font classification and filtering."""

import pytest

from ascii_banner.categories import (
    CATEGORIES,
    FONT_TAGS,
    FONT_METRICS,
    SIZES,
    get_tags,
    get_metrics,
    fonts_by_tag,
    fonts_by_size,
    sort_fonts,
)


# ---------------------------------------------------------------------------
# get_tags
# ---------------------------------------------------------------------------

class TestGetTags:
    def test_known_font(self) -> None:
        tags = get_tags("Standard")
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert "classic" in tags

    def test_case_insensitive(self) -> None:
        tags_lower = get_tags("standard")
        tags_title = get_tags("Standard")
        assert tags_lower == tags_title

    def test_unknown_font_returns_empty(self) -> None:
        tags = get_tags("this_font_does_not_exist_xyz")
        assert tags == []

    def test_big_font(self) -> None:
        tags = get_tags("Big")
        assert "classic" in tags
        assert "sans" in tags

    def test_all_tags_are_valid_categories(self) -> None:
        """Every tag used must be a valid CATEGORIES key."""
        for font_name, tags in FONT_TAGS.items():
            for tag in tags:
                assert tag in CATEGORIES, f"Font '{font_name}' has unknown tag '{tag}'"


# ---------------------------------------------------------------------------
# get_metrics
# ---------------------------------------------------------------------------

class TestGetMetrics:
    def test_known_font(self) -> None:
        m = get_metrics("Standard")
        assert "size" in m
        assert "legibility" in m
        assert m["size"] in SIZES

    def test_unknown_font_defaults(self) -> None:
        m = get_metrics("nonexistent_font_xyz")
        assert m["size"] == "md"
        assert m["legibility"] == 3

    def test_legibility_range(self) -> None:
        """All legibility values should be 1-5."""
        for name, m in FONT_METRICS.items():
            assert 1 <= m["legibility"] <= 5, f"Font '{name}' legibility {m['legibility']} out of range"

    def test_size_values(self) -> None:
        """All sizes should be valid SIZES keys."""
        for name, m in FONT_METRICS.items():
            assert m["size"] in SIZES, f"Font '{name}' has invalid size '{m['size']}'"


# ---------------------------------------------------------------------------
# fonts_by_tag
# ---------------------------------------------------------------------------

class TestFontsByTag:
    def test_classic(self) -> None:
        fonts = fonts_by_tag("classic")
        assert isinstance(fonts, list)
        assert len(fonts) > 0
        assert "Standard" in fonts

    def test_block(self) -> None:
        fonts = fonts_by_tag("block")
        assert len(fonts) > 0

    def test_case_insensitive(self) -> None:
        assert fonts_by_tag("Classic") == fonts_by_tag("classic")

    def test_unknown_tag_empty(self) -> None:
        result = fonts_by_tag("nonexistent_tag_xyz")
        assert result == []

    def test_sorted_alphabetically(self) -> None:
        fonts = fonts_by_tag("classic")
        assert fonts == sorted(fonts, key=str.lower)

    @pytest.mark.parametrize("tag", list(CATEGORIES.keys()))
    def test_all_category_tags_return_results(self, tag: str) -> None:
        """Each defined category should have at least one font."""
        fonts = fonts_by_tag(tag)
        assert len(fonts) > 0, f"Category '{tag}' has no fonts"


# ---------------------------------------------------------------------------
# fonts_by_size
# ---------------------------------------------------------------------------

class TestFontsBySize:
    @pytest.mark.parametrize("size", ["xs", "sm", "md", "lg", "xl"])
    def test_each_size_has_fonts(self, size: str) -> None:
        fonts = fonts_by_size(size)
        assert len(fonts) > 0, f"Size '{size}' has no fonts"

    def test_sorted_alphabetically(self) -> None:
        fonts = fonts_by_size("md")
        assert fonts == sorted(fonts, key=str.lower)

    def test_unknown_size_empty(self) -> None:
        result = fonts_by_size("xxxl")
        assert result == []


# ---------------------------------------------------------------------------
# sort_fonts
# ---------------------------------------------------------------------------

class TestSortFonts:
    @pytest.fixture()
    def sample_fonts(self) -> list[str]:
        return ["Big", "Standard", "Small", "Banner"]

    def test_sort_by_name(self, sample_fonts) -> None:
        result = sort_fonts(sample_fonts, "name")
        assert result == sorted(sample_fonts, key=str.lower)

    def test_sort_by_size(self, sample_fonts) -> None:
        result = sort_fonts(sample_fonts, "size")
        # Verify ordering: smaller sizes come first
        sizes = [get_metrics(n)["size"] for n in result]
        from ascii_banner.categories import SIZE_ORDER
        size_vals = [SIZE_ORDER.get(s, 2) for s in sizes]
        assert size_vals == sorted(size_vals)

    def test_sort_by_legibility(self, sample_fonts) -> None:
        result = sort_fonts(sample_fonts, "legibility")
        # Higher legibility should come first
        legs = [get_metrics(n)["legibility"] for n in result]
        assert legs == sorted(legs, reverse=True)

    def test_default_sort_is_name(self, sample_fonts) -> None:
        result = sort_fonts(sample_fonts)
        assert result == sort_fonts(sample_fonts, "name")

    def test_empty_list(self) -> None:
        assert sort_fonts([]) == []
