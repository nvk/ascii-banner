# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""FIGlet .flf font parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from importlib import resources


@dataclass
class FIGCharacter:
    lines: list[str]
    width: int


@dataclass
class Font:
    name: str = ""
    hardblank: str = "$"
    height: int = 0
    baseline: int = 0
    max_length: int = 0
    old_layout: int = 0
    comment_lines: int = 0
    print_direction: int = 0
    full_layout: int = -1
    comment: str = ""
    characters: dict[int, FIGCharacter] = field(default_factory=dict)

    @property
    def smush_mode(self) -> str:
        if self.full_layout >= 0:
            if self.full_layout & 63:
                return "smushing"
            if self.full_layout & 128:
                return "fitting"
            return "fullwidth"
        if self.old_layout < 0:
            return "fullwidth"
        if self.old_layout == 0:
            return "fitting"
        return "smushing"

    @property
    def smush_rules(self) -> int:
        if self.full_layout >= 0:
            return self.full_layout & 63
        if self.old_layout > 0:
            return self.old_layout
        return 0

    def get_char(self, ch: str) -> FIGCharacter:
        code = ord(ch)
        if code in self.characters:
            return self.characters[code]
        if ord("?") in self.characters:
            return self.characters[ord("?")]
        return FIGCharacter(lines=[""] * self.height, width=0)


def parse(text: str) -> Font:
    """Parse a FIGlet .flf font from a string."""
    # Strip UTF-8 BOM if present
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.split("\n")
    if not lines:
        raise ValueError("Empty font file")

    font = _parse_header(lines[0])
    idx = 1

    # Read comment lines
    comment_parts = []
    for _ in range(font.comment_lines):
        if idx < len(lines):
            comment_parts.append(lines[idx])
            idx += 1
    font.comment = "\n".join(comment_parts)

    # Read required ASCII characters 32-126
    for code in range(32, 127):
        char, idx = _read_character(lines, idx, font.height, font.hardblank)
        font.characters[code] = char

    # Read optional German characters
    for code in [196, 214, 220, 228, 246, 252, 223]:
        try:
            char, idx = _read_character(lines, idx, font.height, font.hardblank)
            font.characters[code] = char
        except (IndexError, ValueError):
            break

    # Read code-tagged characters
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        try:
            code = _parse_code_tag(line)
            idx += 1
            char, idx = _read_character(lines, idx, font.height, font.hardblank)
            font.characters[code] = char
        except (ValueError, IndexError):
            break

    return font


def load(name: str) -> Font:
    """Load a built-in font by name."""
    font_dir = resources.files("ascii_banner") / "fonts"
    font_file = font_dir / f"{name}.flf"
    text = font_file.read_text(encoding="utf-8", errors="replace")
    f = parse(text)
    f.name = name
    return f


def load_file(path: str) -> Font:
    """Load a font from a .flf file path."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    f = parse(text)
    f.name = p.stem
    return f


def list_fonts() -> list[str]:
    """List available built-in font names."""
    font_dir = resources.files("ascii_banner") / "fonts"
    names = []
    for item in font_dir.iterdir():
        if hasattr(item, "name") and item.name.endswith(".flf"):
            names.append(item.name.removesuffix(".flf"))
    return sorted(names)


def _parse_header(header: str) -> Font:
    if not header.startswith("flf2a") and not header.startswith("tlf2a"):
        raise ValueError("Invalid FIGlet font: missing flf2a/tlf2a signature")

    hardblank = header[5]
    if hardblank == " ":
        hardblank = "\x00"  # tlf2a fonts with space hardblank
    fields = header[6:].split()

    if len(fields) < 5:
        raise ValueError(f"Header has too few fields (got {len(fields)}, need 5)")

    font = Font(
        hardblank=hardblank,
        height=int(fields[0]),
        baseline=int(fields[1]),
        max_length=int(fields[2]),
        old_layout=int(fields[3]),
        comment_lines=int(fields[4]),
    )

    if len(fields) > 5:
        font.print_direction = int(fields[5])
    if len(fields) > 6:
        font.full_layout = int(fields[6])

    return font


def _read_character(
    lines: list[str], idx: int, height: int, hardblank: str
) -> tuple[FIGCharacter, int]:
    char_lines = []
    max_width = 0

    for _ in range(height):
        if idx >= len(lines):
            raise IndexError("Unexpected end of font file")
        raw = lines[idx]
        idx += 1
        stripped = _strip_endmark(raw)
        stripped = stripped.replace(hardblank, " ")
        char_lines.append(stripped)
        if len(stripped) > max_width:
            max_width = len(stripped)

    # Pad all lines to same width
    char_lines = [line.ljust(max_width) for line in char_lines]

    return FIGCharacter(lines=char_lines, width=max_width), idx


def _strip_endmark(line: str) -> str:
    line = line.rstrip("\r\n")
    if line.endswith("@@"):
        return line[:-2]
    if line.endswith("@"):
        return line[:-1]
    # Fallback: strip repeated trailing char
    if len(line) > 1:
        if len(line) > 2 and line[-1] == line[-2]:
            return line[:-2]
        return line[:-1]
    return line


def _parse_code_tag(line: str) -> int:
    tag = line.split()[0]
    if tag.startswith("-"):
        return int(tag)
    if tag.startswith(("0x", "0X")):
        return int(tag, 16)
    if tag.startswith("0") and len(tag) > 1:
        return int(tag, 8)
    return int(tag)
