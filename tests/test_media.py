# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.media."""

import pytest

from ascii_banner.animation import AnimationOptions, build_animation
from ascii_banner.canvas import Canvas
from ascii_banner.media import ExportOptions, MediaExportError, export


def test_unknown_export_extension_raises(tmp_path) -> None:
    frames = build_animation(Canvas.from_text("X"), AnimationOptions("reveal"))

    with pytest.raises(MediaExportError, match="unsupported export format"):
        export(frames, tmp_path / "out.xyz", ExportOptions(fps=12))


def test_gif_export_when_pillow_is_available(tmp_path) -> None:
    pytest.importorskip("PIL")
    frames = build_animation(
        Canvas.from_text("GIF"),
        AnimationOptions("unfurl", fps=4, duration=1),
    )
    out = tmp_path / "banner.gif"

    export(frames, out, ExportOptions(fps=4, cell_width=8, cell_height=12))

    assert out.exists()
    assert out.stat().st_size > 0
