# SPDX-License-Identifier: MIT AND Commons-Clause-1.0
# Copyright (c) 2026 nvk
"""Format ASCII art output as code comments."""

from __future__ import annotations

FORMATS: dict[str, dict[str, str]] = {
    "python": {"prefix": "# "},
    "bash": {"prefix": "# "},
    "ruby": {"prefix": "# "},
    "perl": {"prefix": "# "},
    "js": {"prefix": "// "},
    "ts": {"prefix": "// "},
    "go": {"prefix": "// "},
    "rust": {"prefix": "// "},
    "java": {"prefix": "// "},
    "cpp": {"prefix": "// "},
    "c": {"header": "/*", "prefix": " * ", "footer": " */"},
    "css": {"header": "/*", "prefix": " * ", "footer": " */"},
    "html": {"header": "<!--", "prefix": "  ", "footer": "-->"},
    "xml": {"header": "<!--", "prefix": "  ", "footer": "-->"},
    "sql": {"prefix": "-- "},
    "lua": {"prefix": "-- "},
    "hs": {"prefix": "-- "},
}

# Aliases
FORMATS["javascript"] = FORMATS["js"]
FORMATS["typescript"] = FORMATS["ts"]
FORMATS["haskell"] = FORMATS["hs"]
FORMATS["shell"] = FORMATS["bash"]
FORMATS["sh"] = FORMATS["bash"]


def format_comment(text: str, lang: str) -> str:
    """Wrap text as a code comment in the given language."""
    lang = lang.lower().strip()
    fmt = FORMATS.get(lang)
    if fmt is None:
        return text

    lines = text.split("\n")
    result = []

    if "header" in fmt:
        result.append(fmt["header"])

    prefix = fmt.get("prefix", "")
    for line in lines:
        result.append(prefix + line if line else prefix.rstrip())

    if "footer" in fmt:
        result.append(fmt["footer"])

    return "\n".join(result)


def list_formats() -> list[str]:
    """Return sorted list of supported format names."""
    return sorted(set(FORMATS.keys()))
