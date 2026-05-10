# SPDX-License-Identifier: MIT
# Copyright (c) 2026 nvk
"""CLI entry point for ascii-banner."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from . import animation as animod
from . import canvas as canvasmod
from . import color as colormod
from . import media as mediamod
from . import parser, renderer, svg as svgmod
from . import terminal as terminalmod
from .border import wrap as border_wrap, list_styles as border_styles
from .categories import (
    CATEGORIES,
    SIZES,
    fonts_by_size,
    fonts_by_tag,
    get_metrics,
    get_tags,
    sort_fonts,
)
from .formatter import format_comment, list_formats
from .fuzzy import fuzzy_match


def main() -> None:
    # Suppress mechanism
    if os.environ.get("NO_BANNER", "").strip() not in ("", "0"):
        return

    # Handle subcommands before argparse
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            _cmd_list()
            return
        if sys.argv[1] == "tags":
            _cmd_tags()
            return

    args = parse_args()
    _validate_output_args(args)

    if args.quiet:
        return

    # Get input text
    text = " ".join(args.text) if args.text else None

    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Usage: ascii-banner [flags] [text...]")
            print("       ascii-banner list [tag|size]")
            print("       ascii-banner tags")
            print("Try 'ascii-banner --help' for more information.")
            return

    if not text:
        return

    # Detect terminal width
    width = args.width
    if width == 0:
        try:
            width = os.get_terminal_size().columns
        except OSError:
            width = 0

    # Collect font names for multi-font modes
    font_names: list[str] | None = None

    if args.tag:
        font_names = fonts_by_tag(args.tag)
        if not font_names:
            print(f"No fonts found for tag '{args.tag}'")
            print(f"Available tags: {', '.join(sorted(CATEGORIES))}")
            return

    if args.size:
        size_fonts = fonts_by_size(args.size)
        if not size_fonts:
            print(f"No fonts found for size '{args.size}'")
            print(f"Available sizes: xs, sm, md, lg, xl")
            return
        font_names = size_fonts if font_names is None else [n for n in font_names if n in set(size_fonts)]

    if args.all:
        font_names = font_names or parser.list_fonts()

    if font_names is not None:
        if args.svg is not None:
            print("--svg is incompatible with multi-font mode (-a/-t/-s)",
                  file=sys.stderr)
            sys.exit(2)
        if args.animate or args.exports:
            print("--animate/--export is incompatible with multi-font mode (-a/-t/-s)",
                  file=sys.stderr)
            sys.exit(2)
        font_names = sort_fonts(font_names, args.sort)
        _render_multiple(font_names, text, width, args)
        return

    # Single font render
    if args.font_file:
        font = parser.load_file(args.font_file)
    else:
        font = _load_font_fuzzy(args.font)

    output = _render_text(font, text, width, args.justify)

    if args.animate:
        _emit_animation(output, args)
        return

    if args.svg is not None:
        _emit_svg(output, args)
        return

    output = _apply_postprocess(output, args)
    print(output)


def _emit_svg(banner: str, args: argparse.Namespace) -> None:
    """Render the banner as vector SVG and write to file or stdout."""
    for incompatible in ("color", "border", "comment"):
        if getattr(args, incompatible):
            print(f"warning: --{incompatible} ignored when --svg is set",
                  file=sys.stderr)
    try:
        doc = svgmod.to_svg(
            banner,
            mode=args.svg_mode,
            stroke=args.svg_stroke,
            gap=args.svg_gap,
            merge=args.svg_merge,
        )
    except svgmod.UnsupportedGlyphError as e:
        print(f"error: {e}", file=sys.stderr)
        print("hint: SVG output currently supports figlet fonts that use only "
              "block + double-line box-drawing glyphs (e.g. ANSI Shadow).",
              file=sys.stderr)
        sys.exit(1)

    if args.svg == "-":
        sys.stdout.write(doc + "\n")
    else:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(doc + "\n")
        print(f"wrote {args.svg}", file=sys.stderr)


def _emit_animation(banner: str, args: argparse.Namespace) -> None:
    """Build animation frames and play or export them."""
    plain = _apply_plain_postprocess(banner, args)
    final_canvas = canvasmod.Canvas.from_text(plain)
    if args.color:
        final_canvas = canvasmod.apply_color(final_canvas, args.color)

    fps = _animation_fps(args)
    anim_options = animod.AnimationOptions(
        effect=args.animate,
        fps=fps,
        duration=args.duration,
        loop=args.loop,
        seed=args.seed,
        direction=args.direction,
        by=args.by,
        axis=args.axis,
        charset=args.charset,
        intensity=args.intensity,
        palette=args.palette,
    )
    try:
        frames = animod.build_animation(final_canvas, anim_options)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    if args.exports:
        bg = canvasmod.parse_rgb(args.bg)
        if bg is None:
            print(f"error: invalid --bg color: {args.bg}", file=sys.stderr)
            sys.exit(2)
        export_options = mediamod.ExportOptions(
            fps=fps,
            loop=args.loop,
            cell_width=args.cell_width,
            cell_height=args.cell_height,
            bg=bg,
            font_path=args.media_font,
        )
        for target in args.exports:
            try:
                mediamod.export(frames, target, export_options)
            except mediamod.MediaExportError as e:
                print(f"error: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"wrote {target}", file=sys.stderr)
        return

    if sys.stdout.isatty():
        terminalmod.play(frames, fps=fps, loop=args.loop)
    else:
        sys.stdout.write(terminalmod.render_static(frames[-1].canvas) + "\n")


def _load_font_fuzzy(name: str) -> parser.Font:
    """Load font by name with fuzzy matching fallback."""
    try:
        return parser.load(name)
    except Exception:
        pass

    # Fuzzy match
    all_fonts = parser.list_fonts()
    matches = fuzzy_match(name, all_fonts, max_results=3)
    if matches:
        # Use best match
        print(f"Font '{name}' not found. Using '{matches[0]}'.", file=sys.stderr)
        if len(matches) > 1:
            others = ", ".join(matches[1:])
            print(f"  Other matches: {others}", file=sys.stderr)
        return parser.load(matches[0])

    print(f"Font '{name}' not found. Use 'ascii-banner list' to see available fonts.", file=sys.stderr)
    sys.exit(1)


def _render_text(font: parser.Font, text: str, width: int, justify: str) -> str:
    """Render text, handling multi-line input."""
    results = []
    for line in text.split("\n"):
        if not line:
            results.append("")
            continue
        result = renderer.render(font, line, width=width, justify=justify)
        results.append(result)
    return "\n".join(results)


def _apply_postprocess(output: str, args: argparse.Namespace) -> str:
    """Apply border, color, and comment formatting."""
    output = _apply_plain_postprocess(output, args)

    if args.color:
        output = colormod.apply(output, args.color)

    return output


def _apply_plain_postprocess(output: str, args: argparse.Namespace) -> str:
    """Apply post-processing that does not insert ANSI escape codes."""
    if args.border:
        output = border_wrap(output, args.border)

    if args.comment:
        output = format_comment(output, args.comment)

    return output


def _render_multiple(
    font_names: list[str], text: str, width: int, args: argparse.Namespace
) -> None:
    """Render text in multiple fonts with headers."""
    for name in font_names:
        try:
            font = parser.load(name)
            output = _render_text(font, text, width, args.justify)
        except Exception:
            continue
        tags = get_tags(name)
        metrics = get_metrics(name)
        info = f"size:{metrics['size']} legibility:{metrics['legibility']}/5"
        if tags:
            info += f"  [{', '.join(tags)}]"
        print(f"── {name}  ({info}) ──")
        print()
        output = _apply_postprocess(output, args)
        print(output)
        print()


def _cmd_list() -> None:
    """List available fonts, optionally filtered by tag or size."""
    # Check for --preview flag
    preview = "--preview" in sys.argv

    filter_arg = None
    for arg in sys.argv[2:]:
        if arg != "--preview":
            filter_arg = arg
            break

    if filter_arg:
        if filter_arg.lower() in SIZES:
            font_names = fonts_by_size(filter_arg)
            print(f"Fonts of size '{filter_arg}' ({SIZES[filter_arg.lower()]}):")
            for name in font_names:
                _print_font_entry(name, filter_key=filter_arg, preview=preview)
            print(f"\n{len(font_names)} fonts")
            return

        font_names = fonts_by_tag(filter_arg)
        if not font_names:
            print(f"No fonts found for '{filter_arg}'")
            print(f"Available tags: {', '.join(sorted(CATEGORIES))}")
            print(f"Available sizes: {', '.join(SIZES)}")
            return
        print(f"Fonts tagged '{filter_arg}' ({CATEGORIES.get(filter_arg, '')}):")
        for name in font_names:
            _print_font_entry(name, filter_key=filter_arg, preview=preview)
        print(f"\n{len(font_names)} fonts")
    else:
        fonts = parser.list_fonts()
        print("Available fonts:")
        for name in fonts:
            _print_font_entry(name, preview=preview)
        print(f"\n{len(fonts)} fonts available")
        print(f"Filter: ascii-banner list <tag|size>")
        print(f"See tags: ascii-banner tags")


def _print_font_entry(name: str, filter_key: str | None = None, preview: bool = False) -> None:
    """Print a single font entry in list output."""
    m = get_metrics(name)
    tags = get_tags(name)
    if filter_key and filter_key.lower() not in SIZES:
        other = [t for t in tags if t != filter_key]
        extra = f"  +{', '.join(other)}" if other else ""
        print(f"  {name}  size:{m['size']} legibility:{m['legibility']}/5{extra}")
    else:
        tag_str = f"  [{', '.join(tags)}]" if tags else ""
        print(f"  {name}  size:{m['size']} legibility:{m['legibility']}/5{tag_str}")

    if preview:
        try:
            font = parser.load(name)
            output = renderer.render(font, name)
            for line in output.split("\n"):
                print(f"    {line}")
            print()
        except Exception:
            pass


def _cmd_tags() -> None:
    """Show available category tags and sizes with font counts."""
    print("Category tags:\n")
    for tag, desc in sorted(CATEGORIES.items()):
        count = len(fonts_by_tag(tag))
        print(f"  {tag:<12} {desc} ({count} fonts)")

    print(f"\nSizes:\n")
    for size, desc in SIZES.items():
        count = len(fonts_by_size(size))
        print(f"  {size:<12} {desc} ({count} fonts)")

    print(f"\nLegibility: 1 (hard to read) to 5 (very clear)")

    bstyles = ", ".join(border_styles())
    fmts = ", ".join(list_formats())

    print(f"\nBorder styles: {bstyles}")
    print(f"Comment formats: {fmts}")

    print(f"\nUsage:")
    print(f"  ascii-banner list <tag>                    List fonts in a category")
    print(f"  ascii-banner list <size>                   List fonts by size")
    print(f"  ascii-banner list --preview                Show fonts in their own style")
    print(f"  ascii-banner -t <tag> \"text\"                Preview fonts in a category")
    print(f"  ascii-banner -s <size> \"text\"               Preview fonts by size")
    print(f"  ascii-banner --sort legibility \"text\"       Sort by legibility")
    print(f"  ascii-banner -c gradient:red:blue \"text\"   Color gradient")
    print(f"  ascii-banner --border double \"text\"        Add border")
    print(f"  ascii-banner --comment python \"text\"       Format as code comment")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="ascii-banner",
        description="Convert text to ASCII art banners",
        epilog="Commands:\n  list              List fonts (filter: list <tag|size>, preview: list --preview)\n  tags              Show categories, sizes, borders, comment formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ap.add_argument("text", nargs="*", help="text to render")
    ap.add_argument("-f", "--font", default="standard", help="font name (supports fuzzy matching)")
    ap.add_argument("-F", "--font-file", help="load font from a .flf file path")
    ap.add_argument("-a", "--all", action="store_true", help="show text in all available fonts")
    ap.add_argument("-t", "--tag", help="filter fonts by tag (e.g. -t block)")
    ap.add_argument("-s", "--size", choices=["xs", "sm", "md", "lg", "xl"], help="filter fonts by size")
    ap.add_argument("--sort", choices=["name", "size", "legibility"], default="name",
                    help="sort order for multi-font output (default: name)")
    ap.add_argument("-w", "--width", type=int, default=0, help="max output width")
    ap.add_argument("-c", "--color",
                    help="color: name, hex, rainbow, gradient:c1:c2, gradient:rainbow")
    ap.add_argument("-j", "--justify", default="left", choices=["left", "center", "right"],
                    help="justification (default: left)")
    ap.add_argument("--border", choices=["single", "double", "rounded", "heavy", "ascii"],
                    help="wrap output in a border box")
    ap.add_argument("--comment",
                    help="format as code comment (python, js, c, bash, html, ...)")
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress output")

    ap.add_argument("--svg", nargs="?", const="-", default=None, metavar="PATH",
                    help="emit vector SVG instead of terminal output "
                         "(no value or '-' = stdout)")
    ap.add_argument("--svg-mode", choices=["default", "inset", "extend"],
                    default="extend",
                    help="SVG block rendering mode (default: extend)")
    ap.add_argument("--svg-stroke", type=float, default=15,
                    help="SVG: thickness of each line in a double-line glyph")
    ap.add_argument("--svg-gap", type=float, default=20,
                    help="SVG: gap between the two parallel lines of a double")
    ap.add_argument("--svg-merge", action="store_true",
                    help="SVG: merge adjacency-aligned rects (smaller file)")

    ap.add_argument("--animate", type=str.lower, choices=animod.EFFECTS,
                    help="play or export a canned animation")
    ap.add_argument("--export", dest="exports", action="append", metavar="PATH",
                    help="export animation to .gif, .mp4, .webm, or .webp "
                         "(repeatable)")
    ap.add_argument("--fps", type=int, default=None,
                    help="animation frames per second (default: 12, or 24 for video)")
    ap.add_argument("--duration", type=float,
                    help="animation duration in seconds")
    ap.add_argument("--loop", type=int, default=1,
                    help="animation loop count; 0 means infinite where supported")
    ap.add_argument("--seed", type=int,
                    help="deterministic seed for randomized animations")
    ap.add_argument("--direction", choices=animod.DIRECTIONS, default="left",
                    help="animation direction for wipe/slide-style effects")
    ap.add_argument("--by", choices=animod.BY_MODES, default="char",
                    help="animation reveal unit for reveal/print effects")
    ap.add_argument("--axis", choices=animod.AXES, default="both",
                    help="animation axis for middleout/slice/waves-style effects")
    ap.add_argument("--charset",
                    help="character set for matrix/decrypt/glitch effects "
                         "(ascii, binary, hex, or literal characters)")
    ap.add_argument("--intensity", type=float, default=0.35,
                    help="effect intensity from 0 to 1")
    ap.add_argument("--palette", choices=animod.PALETTES, default="accent",
                    help="animation color palette (default: accent)")
    ap.add_argument("--cell-width", type=int, default=10,
                    help="media export cell width in pixels")
    ap.add_argument("--cell-height", type=int, default=18,
                    help="media export cell height in pixels")
    ap.add_argument("--media-font",
                    help="optional monospace TTF/OTF/TTC path for media export")
    ap.add_argument("--bg", default="black",
                    help="media export background color name or #rrggbb")

    return ap.parse_args()


def _validate_output_args(args: argparse.Namespace) -> None:
    if args.exports and not args.animate:
        print("error: --export requires --animate", file=sys.stderr)
        sys.exit(2)
    if args.animate and args.svg is not None:
        print("error: --animate is incompatible with --svg", file=sys.stderr)
        sys.exit(2)
    if args.fps is not None and args.fps <= 0:
        print("error: --fps must be greater than zero", file=sys.stderr)
        sys.exit(2)
    if args.duration is not None and args.duration <= 0:
        print("error: --duration must be greater than zero", file=sys.stderr)
        sys.exit(2)
    if args.loop < 0:
        print("error: --loop must be zero or greater", file=sys.stderr)
        sys.exit(2)
    if not 0 <= args.intensity <= 1:
        print("error: --intensity must be between 0 and 1", file=sys.stderr)
        sys.exit(2)
    if args.charset == "":
        print("error: --charset cannot be empty", file=sys.stderr)
        sys.exit(2)
    if args.cell_width <= 0 or args.cell_height <= 0:
        print("error: --cell-width and --cell-height must be greater than zero",
              file=sys.stderr)
        sys.exit(2)
    if args.media_font and not Path(args.media_font).exists():
        print(f"error: --media-font not found: {args.media_font}", file=sys.stderr)
        sys.exit(2)


def _animation_fps(args: argparse.Namespace) -> int:
    if args.fps is not None:
        return args.fps
    if args.exports:
        video_exts = {".mp4", ".webm"}
        if any(Path(target).suffix.lower() in video_exts for target in args.exports):
            return 24
    return 12


if __name__ == "__main__":
    main()
