"""Import LCSC parts into the global KiCad library via easyeda2kicad."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from kicad_cursor_config import REPO_ROOT, resolveSymbolLibraryBase

FIX_SCRIPT = REPO_ROOT / "scripts" / "fix-symbol-lib.py"


def defaultOutputBase() -> Path:
    libraryDir = resolveSymbolLibraryBase()
    return libraryDir / "global"


def runFetch(lcscId: str, output: Path, mode: list[str]) -> int:
    cmd = [
        "easyeda2kicad",
        *mode,
        f"--lcsc_id={lcscId}",
        f"--output={output.as_posix()}",
    ]
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def runFix(symbolFile: Path) -> int:
    cmd = [sys.executable, str(FIX_SCRIPT), str(symbolFile)]
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lcscId", help="LCSC part id, e.g. C80200")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output library base path (no extension; default from kicad-cursor.yaml)",
    )
    parser.add_argument("--symbol", action="store_true", help="Symbol only")
    parser.add_argument("--footprint", action="store_true", help="Footprint only")
    parser.add_argument("--3d", dest="model3d", action="store_true", help="3D model only")
    parser.add_argument(
        "--skip-fix",
        action="store_true",
        help="Skip fix-symbol-lib repair after fetch",
    )
    args = parser.parse_args()

    lcscId = args.lcscId.strip().upper()
    if not lcscId.startswith("C"):
        lcscId = f"C{lcscId}"

    mode: list[str] = []
    if args.symbol:
        mode.append("--symbol")
    if args.footprint:
        mode.append("--footprint")
    if args.model3d:
        mode.append("--3d")
    if not mode:
        mode = ["--full"]

    try:
        outputBase = args.output or defaultOutputBase()
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if runFetch(lcscId, outputBase, mode) != 0:
        return 1

    if args.skip_fix or args.footprint or args.model3d:
        return 0

    symbolFile = outputBase.with_suffix(".kicad_sym")
    if runFix(symbolFile) != 0:
        return 1

    print(f"Imported {lcscId} into {outputBase}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
