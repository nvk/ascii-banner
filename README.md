# ascii-banner

![ascii-banner hero](screenshots/hero.svg)

Convert text to ASCII art banners using FIGlet fonts. 328 built-in fonts, color output, borders, comment formatting, and fuzzy font search -- all with zero dependencies.

**Website**: [ascii-banner.com](https://ascii-banner.com) | **Repository**: [github.com/nvk/ascii-banner](https://github.com/nvk/ascii-banner)

## Install

```bash
# Homebrew (macOS/Linux)
brew install nvk/tap/ascii-banner

# pip
pip install ascii-banner
```

## Quick Start

```bash
# Default font (standard)
ascii-banner "Hello"

# Pick a font
ascii-banner -f Doom "Hello"

# Pipe input
echo "Hello" | ascii-banner -f Big

# Color + border
ascii-banner -f Slant -c red --border rounded "Deploy"
```

![fonts and colors](screenshots/fonts-showcase.svg)

## Fonts

328 bundled FIGlet fonts, each tagged with categories and rated for size (xs/sm/md/lg/xl) and legibility (1-5).

### Browse fonts

```bash
# List all fonts
ascii-banner list

# Filter by tag
ascii-banner list block

# Filter by size
ascii-banner list sm

# Preview fonts rendered in their own style
ascii-banner list --preview

# Show all available tags, sizes, and other options
ascii-banner tags
```

### Preview fonts with your text

![tag browsing](screenshots/tags.svg)

```bash
# Show text in all fonts
ascii-banner --all "Test"

# Show text in fonts matching a tag
ascii-banner -t gothic "Test"

# Show text in fonts matching a size
ascii-banner -s xl "Test"

# Combine tag + size
ascii-banner -t block -s md "Test"

# Sort by legibility (highest first)
ascii-banner -t classic --sort legibility "Test"
```

### Category tags

| Tag | Description |
|---|---|
| `3d` | 3D effects, depth, perspective |
| `block` | Heavy block/box characters, filled shapes |
| `bubble` | Rounded, bubble-like characters |
| `classic` | Traditional FIGlet style |
| `cursive` | Script, handwriting, flowing |
| `decorative` | Ornamental, fancy, elaborate |
| `digital` | LED, LCD, dot matrix, pixel |
| `gothic` | Dark, medieval, blackletter |
| `graffiti` | Street art, urban style |
| `lean` | Thin, lightweight strokes |
| `mini` | Very small, compact (1-3 lines) |
| `mono` | Monospace, fixed-width terminal style |
| `sans` | Clean sans-serif letterforms |
| `serif` | Serif letterforms |
| `shadow` | Shadow effects |
| `slant` | Italic/slanted/oblique |
| `tech` | Futuristic, sci-fi, cyber |
| `weird` | Abstract, artistic, hard to read |

### Size classes

| Size | Height |
|---|---|
| `xs` | 1-3 lines |
| `sm` | 4-5 lines |
| `md` | 6-8 lines |
| `lg` | 9-12 lines |
| `xl` | 13+ lines |

## Colors

Apply color to output with `-c` / `--color`. Requires a terminal that supports ANSI escape codes.

![rainbow colors](screenshots/rainbow.svg)

```bash
# Named colors: black, red, green, yellow, blue, magenta, cyan, white
ascii-banner -c green "OK"

# Hex color
ascii-banner -c "#ff6600" "Fire"

# Rainbow (cycles per character)
ascii-banner -c rainbow "Party"

# Two-color gradient (horizontal)
ascii-banner -c gradient:red:blue "Fade"

# Gradient supports named colors, hex, and extra names: orange, pink, purple
ascii-banner -c gradient:#ff0000:#00ff00 "Xmas"

# Smooth rainbow gradient (full spectrum)
ascii-banner -c gradient:rainbow "Spectrum"
```

## Borders

Wrap output in a box with `--border`. Five styles available:

![border example](screenshots/border.svg)

```bash
# Single line
ascii-banner --border single "Hi"
# ┌──────────────┐
# │  _   _ _     │
# │ | | | (_)    │
# │ | |_| |_     │
# │ |  _  | |    │
# │ |_| |_|_|    │
# └──────────────┘

# Double line
ascii-banner --border double "Hi"
# ╔══════════════╗
# ║  ...         ║
# ╚══════════════╝

# Rounded corners
ascii-banner --border rounded "Hi"
# ╭──────────────╮
# │  ...         │
# ╰──────────────╯

# Heavy/thick
ascii-banner --border heavy "Hi"
# ┏━━━━━━━━━━━━━━┓
# ┃  ...         ┃
# ┗━━━━━━━━━━━━━━┛

# ASCII (portable)
ascii-banner --border ascii "Hi"
# +----------------+
# |  ...           |
# +----------------+
```

## Comment Formatting

Wrap output as a source code comment with `--comment`. Useful for embedding banners in code.

![comment formatting](screenshots/comment.svg)

```bash
# Python / Bash / Ruby / Perl
ascii-banner --comment python "api"
#    __ _ _ __  _
#   / _` | '_ \| |
#  | (_| | |_) | |
#   \__,_| .__/|_|
#         |_|

# JavaScript / TypeScript / Go / Rust / Java / C++
ascii-banner --comment js "api"
//    __ _ _ __  _
//   / _` | '_ \| |
//  | (_| | |_) | |
//   \__,_| .__/|_|
//         |_|

# C / CSS (block comment)
ascii-banner --comment c "api"
/*
 *    __ _ _ __  _
 *   / _` | '_ \| |
 *  | (_| | |_) | |
 *   \__,_| .__/|_|
 *         |_|
 */

# HTML / XML
ascii-banner --comment html "api"
<!--
     __ _ _ __  _
    / _` | '_ \| |
   | (_| | |_) | |
    \__,_| .__/|_|
          |_|
-->

# SQL / Lua / Haskell
ascii-banner --comment sql "api"
--    __ _ _ __  _
--   / _` | '_ \| |
--  | (_| | |_) | |
--   \__,_| .__/|_|
--         |_|
```

Supported languages: `bash`, `c`, `cpp`, `css`, `go`, `haskell`/`hs`, `html`, `java`, `javascript`/`js`, `lua`, `perl`, `python`, `ruby`, `rust`, `shell`/`sh`, `sql`, `typescript`/`ts`, `xml`.

## Fuzzy Search

Misspell a font name and ascii-banner will suggest the closest match:

```bash
$ ascii-banner -f stanard "Hi"
Font 'stanard' not found. Using 'Standard'.

$ ascii-banner -f blok "Hi"
Font 'blok' not found. Using 'Block'.
  Other matches: Blocks, Bloody
```

Fuzzy matching uses substring search, character sequence matching, and Levenshtein edit distance to find the best result.

## SVG Output

Emit a banner as pure-vector SVG (rectangles only — no font dependency,
no rasterization). Useful for stickers, vinyl plotters, laser cutters,
or any time you want a resolution-independent version of the banner.

```bash
# Write SVG to file
ascii-banner -f "ANSI Shadow" --svg out.svg "LLM WIKI"

# Write SVG to stdout
ascii-banner -f "ANSI Shadow" --svg - "LLM WIKI" > out.svg
```

`--svg-mode` controls how the █ block aligns with the shadow band:

- `extend` (default) — front face stays solid, shadow attaches as a continuous outline. Best for cutter use.
- `default` — authentic figlet ANSI-Shadow look with a visible offset between front face and shadow.
- `inset` — fragmented 8-bit / pixel-glitch aesthetic.

`--svg-merge` collapses adjacent axis-aligned rects (e.g. `═══════` →
one wide rect), shrinking the file ~60% with byte-identical render.

SVG output currently supports figlet fonts that use only block +
double-line box-drawing glyphs (ANSI Shadow and similar). Other fonts
fail loudly with the offending codepoint.

## Animations and Media Export

Play canned terminal animations, or export them for the web.

```bash
# Play in an interactive terminal
ascii-banner --animate reveal "Deploy"
ascii-banner -f "ANSI Shadow" -c gradient:green:cyan --animate matrix "LLM WIKI"

# Export animated assets
ascii-banner --animate unfurl --export deploy.gif "Deploy"
ascii-banner --animate matrix --seed 7 --duration 3 --export banner.mp4 "Launch"
ascii-banner --animate reveal --export banner.mp4 --export banner.webm "Launch"
```

Effects: `reveal`, `unfurl`, `matrix`, `print`, `random`, `decrypt`,
`wipe`, `middleout`, `slice`, `slide`, `scan`, `colorshift`, `glitch`,
`waves`, `vhs`, `rain`, `sparkle`, `fireworks`, `laser`,
`errorcorrect`, `pour`, `burn`, `smoke`, `pipes`, `starfield`,
`bubbles`, `swarm`, `blackhole`, `synthgrid`, `thunderstorm`.

Effect modifiers:

```bash
ascii-banner --animate decrypt --charset hex --seed 7 "Secure"
ascii-banner --animate wipe --direction right "Deploy"
ascii-banner --animate print --by line "Release"
ascii-banner --animate colorshift --palette rainbow "Party"
ascii-banner --animate glitch --intensity 0.2 "Incident"
```

GIF and WebP export require the optional media extra:

```bash
pip install "ascii-banner[media]"
```

MP4 and WebM export also require `ffmpeg` on your `PATH`. GIF is the
lowest-friction format for READMEs and issue trackers; MP4/H.264 and
WebM/VP9 are better for normal web pages.

## Suppress Output

```bash
# Flag: suppress all output
ascii-banner -q "hidden"
ascii-banner --quiet "hidden"

# Environment variable: suppress all output (any value except "" and "0")
NO_BANNER=1 ascii-banner "hidden"
```

Useful for conditionally disabling banners in scripts or CI.

## Full Flag Reference

| Flag | Short | Description |
|---|---|---|
| `text` | | Text to render (positional, or pipe via stdin) |
| `--font NAME` | `-f` | Font name (default: `standard`). Supports fuzzy matching |
| `--font-file PATH` | `-F` | Load a `.flf` font from a file path |
| `--all` | `-a` | Render text in all available fonts |
| `--tag TAG` | `-t` | Filter fonts by category tag |
| `--size SIZE` | `-s` | Filter fonts by size (`xs`, `sm`, `md`, `lg`, `xl`) |
| `--sort KEY` | | Sort multi-font output: `name`, `size`, `legibility` (default: `name`) |
| `--width N` | `-w` | Max output width (default: terminal width) |
| `--color COLOR` | `-c` | Color: name, `#hex`, `rainbow`, `gradient:c1:c2`, `gradient:rainbow` |
| `--justify ALIGN` | `-j` | Justification: `left`, `center`, `right` (default: `left`) |
| `--border STYLE` | | Border box: `single`, `double`, `rounded`, `heavy`, `ascii` |
| `--comment LANG` | | Wrap as code comment for the given language |
| `--quiet` | `-q` | Suppress all output |
| `--animate EFFECT` | | Play/export animation effect |
| `--export PATH` | | Export animation to `.gif`, `.mp4`, `.webm`, or `.webp`; repeatable |
| `--fps N` | | Animation frames per second |
| `--duration SECONDS` | | Animation duration |
| `--loop N` | | Animation loop count; `0` means infinite where supported |
| `--seed N` | | Deterministic seed for randomized animations |
| `--direction DIR` | | Direction for wipe/slide effects: `left`, `right`, `up`, `down` |
| `--by MODE` | | Reveal unit: `char`, `line`, `row`, `column` |
| `--axis AXIS` | | Axis for effects such as `middleout`/`slice`: `horizontal`, `vertical`, `both`, `rows`, `cols` |
| `--charset CHARS` | | Character set for matrix/decrypt/glitch: `ascii`, `binary`, `hex`, or literal chars |
| `--intensity N` | | Effect intensity from `0` to `1` |
| `--palette NAME` | | Animation palette: `accent`, `rainbow`, `fire`, `ocean` |
| `--cell-width N` | | Media export cell width in pixels |
| `--cell-height N` | | Media export cell height in pixels |
| `--media-font PATH` | | Optional monospace font file for media export |
| `--bg COLOR` | | Media export background color name or `#rrggbb` |

### Subcommands

| Command | Description |
|---|---|
| `ascii-banner list` | List all fonts with size and legibility info |
| `ascii-banner list <tag\|size>` | List fonts filtered by tag or size class |
| `ascii-banner list --preview` | List fonts with a rendered preview |
| `ascii-banner tags` | Show all tags, sizes, border styles, and comment formats |

## History

Curious about the origins of ASCII art? Check out [asciihistory.com](https://asciihistory.com).

## License

MIT -- Copyright (c) 2026 nvk

Bundled FIGlet font files (`.flf`) retain their original licenses as specified in each font's comment header.
