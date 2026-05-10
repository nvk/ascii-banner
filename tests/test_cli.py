# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""Tests for ascii_banner.cli — CLI subprocess tests."""

import subprocess
import sys

import pytest


def run_banner(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run ascii-banner as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "ascii_banner", *args],
        capture_output=True,
        text=True,
        timeout=30,
        input=input_text,
    )


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------

class TestCliBasicRender:
    def test_simple_text(self) -> None:
        result = run_banner("Hello")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0

    def test_multiword_text(self) -> None:
        result = run_banner("Hello", "World")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0

    def test_custom_font(self) -> None:
        result = run_banner("-f", "Big", "Hi")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0

    def test_output_is_multiline(self) -> None:
        result = run_banner("Hi")
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 1


# ---------------------------------------------------------------------------
# --quiet flag
# ---------------------------------------------------------------------------

class TestCliQuiet:
    def test_quiet_flag(self) -> None:
        result = run_banner("--quiet", "Hello")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_quiet_short_flag(self) -> None:
        result = run_banner("-q", "Hello")
        assert result.returncode == 0
        assert result.stdout == ""


# ---------------------------------------------------------------------------
# list subcommand
# ---------------------------------------------------------------------------

class TestCliList:
    def test_list_fonts(self) -> None:
        result = run_banner("list")
        assert result.returncode == 0
        assert "standard" in result.stdout.lower() or "Standard" in result.stdout

    def test_list_by_tag(self) -> None:
        result = run_banner("list", "classic")
        assert result.returncode == 0
        assert "standard" in result.stdout

    def test_list_by_size(self) -> None:
        result = run_banner("list", "xs")
        assert result.returncode == 0
        assert "fonts" in result.stdout.lower()

    def test_list_shows_count(self) -> None:
        result = run_banner("list")
        assert "fonts" in result.stdout.lower()


# ---------------------------------------------------------------------------
# tags subcommand
# ---------------------------------------------------------------------------

class TestCliTags:
    def test_tags(self) -> None:
        result = run_banner("tags")
        assert result.returncode == 0
        assert "classic" in result.stdout
        assert "block" in result.stdout

    def test_tags_shows_sizes(self) -> None:
        result = run_banner("tags")
        assert "xs" in result.stdout or "Extra small" in result.stdout

    def test_tags_shows_border_styles(self) -> None:
        result = run_banner("tags")
        assert "Border styles" in result.stdout or "border" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

class TestCliOptions:
    def test_color_option(self) -> None:
        result = run_banner("-c", "red", "Hi")
        assert result.returncode == 0
        # Output should contain ANSI codes
        assert "\033[" in result.stdout

    def test_border_option(self) -> None:
        result = run_banner("--border", "ascii", "Hi")
        assert result.returncode == 0
        assert "+" in result.stdout  # ASCII border uses +

    def test_comment_option(self) -> None:
        result = run_banner("--comment", "python", "Hi")
        assert result.returncode == 0
        assert "# " in result.stdout

    def test_justify_center(self) -> None:
        result = run_banner("-j", "center", "-w", "120", "A")
        assert result.returncode == 0

    def test_svg_stdout_dash(self) -> None:
        result = run_banner("-f", "ANSI Shadow", "--svg", "-", "LLM")
        assert result.returncode == 0
        assert result.stdout.startswith("<?xml")
        assert "<svg " in result.stdout


# ---------------------------------------------------------------------------
# Animation
# ---------------------------------------------------------------------------

class TestCliAnimation:
    def test_animate_non_tty_prints_final_frame(self) -> None:
        result = run_banner("--animate", "reveal", "Hi")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0
        assert "\033[H" not in result.stdout

    def test_animate_with_color_preserves_ansi_color(self) -> None:
        result = run_banner("--animate", "unfurl", "-c", "red", "Hi")
        assert result.returncode == 0
        assert "\033[38;2;255;0;0m" in result.stdout

    def test_export_requires_animate(self, tmp_path) -> None:
        result = run_banner("--export", str(tmp_path / "out.gif"), "Hi")
        assert result.returncode == 2
        assert "--export requires --animate" in result.stderr

    def test_animate_rejects_svg(self) -> None:
        result = run_banner("--animate", "reveal", "--svg", "-", "Hi")
        assert result.returncode == 2
        assert "incompatible with --svg" in result.stderr

    def test_animate_rejects_multifont(self) -> None:
        result = run_banner("--animate", "reveal", "-t", "classic", "Hi")
        assert result.returncode == 2
        assert "incompatible with multi-font" in result.stderr

    def test_animate_accepts_shared_effect_options(self) -> None:
        result = run_banner(
            "--animate", "decrypt",
            "--charset", "hex",
            "--direction", "right",
            "--axis", "rows",
            "--by", "line",
            "--intensity", "0.2",
            "--palette", "accent",
            "Hi",
        )
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0

    def test_animate_rejects_bad_intensity(self) -> None:
        result = run_banner("--animate", "glitch", "--intensity", "2", "Hi")
        assert result.returncode == 2
        assert "--intensity" in result.stderr


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestCliEdgeCases:
    def test_no_args_shows_usage(self) -> None:
        result = run_banner()
        assert result.returncode == 0
        # Output goes to stdout; when run in a non-TTY subprocess stdin is not a tty
        # so it tries to read stdin (which is empty), producing no output
        # This is correct behavior — no TTY + no args + no stdin = no output

    def test_no_banner_env(self) -> None:
        """NO_BANNER=1 should suppress all output."""
        import os
        env = os.environ.copy()
        env["NO_BANNER"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "ascii_banner", "Hello"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_multifont_preserves_stdin_newlines(self) -> None:
        result = run_banner("-t", "shadow", "-s", "sm", input_text="A\nB")
        assert result.returncode == 0
        assert "?" not in result.stdout
