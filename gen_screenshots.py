"""Generate terminal-style screenshots using rich Console SVG export."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.text import Text
from rich.terminal_theme import DIMMED_MONOKAI

DIR = Path(__file__).parent / "screenshots"
DIR.mkdir(exist_ok=True)


def run(*args: str) -> str:
    r = subprocess.run(
        [sys.executable, "-m", "ascii_banner", *args],
        capture_output=True, text=True,
    )
    return r.stdout.rstrip("\n")


def save_svg(content: str, filename: str, title: str = "ascii-banner", width: int = 100) -> None:
    console = Console(file=None, record=True, width=width, force_terminal=True)
    console.print(Text.from_ansi(content))
    svg = console.export_svg(title=title, theme=DIMMED_MONOKAI)
    (DIR / filename).write_text(svg)
    print(f"  {filename}")


def save_svg_with_cmd(cmd: str, args: list[str], filename: str, width: int = 100) -> None:
    output = run(*args)
    console = Console(file=None, record=True, width=width, force_terminal=True)
    prompt = Text("$ ", style="green")
    prompt.append(cmd, style="white")
    console.print(prompt)
    console.print()
    console.print(Text.from_ansi(output))
    svg = console.export_svg(title="ascii-banner", theme=DIMMED_MONOKAI)
    (DIR / filename).write_text(svg)
    print(f"  {filename}")


THEME = DIMMED_MONOKAI


def main() -> None:
    print("Generating screenshots...\n")

    # 1. Hero
    save_svg_with_cmd(
        'ascii-banner -f Slant "ASCII BANNER"',
        ["-f", "Slant", "ASCII BANNER"],
        "hero.svg", width=80,
    )

    # 2. Fonts showcase
    out1 = run("-f", "Doom", "Hello World")
    out2 = run("-f", "Big", "Crypto")
    console = Console(file=None, record=True, width=80, force_terminal=True)
    console.print(Text("$ ", style="green") + Text('ascii-banner -f Doom "Hello World"', style="white"))
    console.print()
    console.print(Text.from_ansi(out1))
    console.print()
    console.print(Text("$ ", style="green") + Text('ascii-banner -f Big "Crypto"', style="white"))
    console.print()
    console.print(Text.from_ansi(out2))
    (DIR / "fonts-showcase.svg").write_text(console.export_svg(title="ascii-banner", theme=THEME))
    print("  fonts-showcase.svg")

    # 3. Rainbow
    save_svg_with_cmd(
        'ascii-banner -c rainbow "Hello World"',
        ["-f", "standard", "-c", "rainbow", "Hello World"],
        "rainbow.svg", width=60,
    )

    # 4. Border
    save_svg_with_cmd(
        'ascii-banner --border rounded "HACK THE PLANET"',
        ["--border", "rounded", "HACK THE PLANET"],
        "border.svg", width=95,
    )

    # 5. Comment formatting
    save_svg_with_cmd(
        'ascii-banner --comment python -f small "CONFIG"',
        ["--comment", "python", "-f", "small", "CONFIG"],
        "comment.svg", width=50,
    )

    # 6. Tag browsing (first 3 gothic fonts)
    output = run("-t", "gothic", "-s", "md", "DOOM")
    lines = output.split("\n")
    trimmed, count = [], 0
    for line in lines:
        if line.startswith("── "):
            count += 1
            if count > 3:
                break
        trimmed.append(line)
    console = Console(file=None, record=True, width=80, force_terminal=True)
    console.print(Text("$ ", style="green") + Text('ascii-banner -t gothic -s md "DOOM"', style="white"))
    console.print()
    console.print(Text.from_ansi("\n".join(trimmed)))
    (DIR / "tags.svg").write_text(console.export_svg(title="ascii-banner", theme=THEME))
    print("  tags.svg")

    # 7. Gradient
    save_svg_with_cmd(
        'ascii-banner -c gradient:red:cyan "GRADIENT"',
        ["-f", "standard", "-c", "gradient:red:cyan", "GRADIENT"],
        "gradient.svg", width=60,
    )

    print("\nDone! SVG files in screenshots/")


if __name__ == "__main__":
    main()
