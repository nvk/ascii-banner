# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.animation."""

import pytest

from ascii_banner.animation import EFFECTS, AnimationOptions, build_animation
from ascii_banner.canvas import Canvas


def test_reveal_ends_with_final_canvas() -> None:
    final = Canvas.from_text("AB\nCD")
    frames = build_animation(final, AnimationOptions("reveal", fps=4, duration=1))

    assert len(frames) == 4
    assert frames[0].canvas.width == final.width
    assert frames[0].canvas.height == final.height
    assert frames[-1].canvas == final


def test_unfurl_starts_blank_and_ends_final() -> None:
    final = Canvas.from_text("ABCD")
    frames = build_animation(final, AnimationOptions("unfurl", fps=4, duration=1))

    assert frames[0].canvas.to_text(trim=True) == ""
    assert frames[-1].canvas == final


def test_matrix_is_deterministic_with_seed() -> None:
    final = Canvas.from_text("MATRIX")
    options = AnimationOptions("matrix", fps=5, duration=1, seed=7)

    first = build_animation(final, options)
    second = build_animation(final, options)

    assert [frame.canvas for frame in first] == [frame.canvas for frame in second]
    assert first[-1].canvas == final


@pytest.mark.parametrize("effect", EFFECTS)
def test_effect_ends_with_final_canvas(effect: str) -> None:
    final = Canvas.from_text("AB\nCD", fg=(255, 128, 0))
    options = AnimationOptions(effect, fps=4, duration=1, seed=7)

    frames = build_animation(final, options)

    assert len(frames) == 4
    assert frames[-1].canvas == final
    assert all(frame.canvas.width == final.width for frame in frames)
    assert all(frame.canvas.height == final.height for frame in frames)


@pytest.mark.parametrize("effect", EFFECTS)
def test_effect_is_deterministic_with_seed(effect: str) -> None:
    final = Canvas.from_text("SEED", fg=(255, 128, 0))
    options = AnimationOptions(effect, fps=5, duration=1, seed=21)

    first = build_animation(final, options)
    second = build_animation(final, options)

    assert [frame.canvas for frame in first] == [frame.canvas for frame in second]


def test_orange_text_drives_effect_accent() -> None:
    orange = (255, 128, 0)
    final = Canvas.from_text("BTC", fg=orange)

    frames = build_animation(
        final,
        AnimationOptions("decrypt", fps=4, duration=1, seed=3),
    )

    assert any(cell.fg == orange for row in frames[0].canvas.cells for cell in row)


def test_wipe_direction_right_starts_from_right_edge() -> None:
    final = Canvas.from_text("ABCD")
    frames = build_animation(
        final,
        AnimationOptions("wipe", fps=4, duration=1, direction="right"),
    )

    assert frames[1].canvas.to_text().rstrip().endswith("D")


def test_unknown_effect_raises() -> None:
    final = Canvas.from_text("X")

    with pytest.raises(ValueError, match="unknown animation effect"):
        build_animation(final, AnimationOptions("unknown"))


def test_invalid_fps_raises() -> None:
    final = Canvas.from_text("X")

    with pytest.raises(ValueError, match="fps"):
        build_animation(final, AnimationOptions("reveal", fps=0))


def test_invalid_direction_raises() -> None:
    final = Canvas.from_text("X")

    with pytest.raises(ValueError, match="direction"):
        build_animation(final, AnimationOptions("wipe", direction="sideways"))


def test_invalid_intensity_raises() -> None:
    final = Canvas.from_text("X")

    with pytest.raises(ValueError, match="intensity"):
        build_animation(final, AnimationOptions("glitch", intensity=1.5))
