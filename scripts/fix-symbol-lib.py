#!/usr/bin/env python3
"""Repair symbol library file after easyeda2kicad 1.x appends symbols outside the library block."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from kicad_cursor_config import resolveSymbolLibraryBase

ORPHAN_PATTERN = re.compile(
    r"\n\)\n(\s*\(symbol )",
    re.MULTILINE,
)


def defaultSymbolFile() -> Path:
    return resolveSymbolLibraryBase() / "global.kicad_sym"


def fixContent(content: str) -> tuple[str, bool]:
    if not ORPHAN_PATTERN.search(content):
        return content, False
    fixed = ORPHAN_PATTERN.sub(r"\n\1", content)
    return fixed, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "symbolFile",
        nargs="?",
        type=Path,
        help="Path to symbol library .kicad_sym (default from kicad-cursor.yaml)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if malformed, 0 if OK",
    )
    args = parser.parse_args()

    try:
        path = args.symbolFile or defaultSymbolFile()
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    content = path.read_text(encoding="utf-8")
    fixed, changed = fixContent(content)

    if args.check:
        return 1 if changed else 0

    if not changed:
        print(f"OK: {path}")
        return 0

    path.write_text(fixed, encoding="utf-8")
    print(f"Fixed orphaned symbols in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
