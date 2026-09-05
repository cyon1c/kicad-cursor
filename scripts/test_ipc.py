"""Basic connectivity test for KiCad 10 IPC API."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def findDefaultSocket() -> str | None:
    tempKicad = Path(tempfile.gettempdir()) / "kicad"
    if not tempKicad.is_dir():
        return None

    candidates = sorted(tempKicad.glob("api*.sock"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None

    return str(candidates[0])


def main() -> int:
    try:
        from kipy import KiCad
        from kipy.errors import ApiError
    except ImportError:
        print("FAIL: kicad-python not installed. Run: uv sync", file=sys.stderr)
        return 2

    socketPath = os.environ.get("KICAD_API_SOCKET") or findDefaultSocket()
    print(f"API socket: {socketPath or '(auto-detect)'}")

    try:
        kicad = KiCad(socket_path=socketPath) if socketPath else KiCad()
    except Exception as exc:
        print(f"FAIL: Could not connect to KiCad IPC API: {exc}", file=sys.stderr)
        print("Ensure KiCad 10 is running with IPC enabled (Preferences → Plugins).", file=sys.stderr)
        return 1

    print(f"OK: Connected to KiCad {kicad.get_version()}")

    try:
        board = kicad.get_board()
        footprints = board.get_footprints()
        print(f"OK: Active PCB has {len(footprints)} footprint(s)")
    except ApiError as exc:
        print(f"NOTE: PCB editor not ready — {exc}")
        print("      Open your board in PCB Editor (not just the project manager), then re-run.")
        return 0
    except Exception as exc:
        print(f"NOTE: Could not read board — {exc}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
