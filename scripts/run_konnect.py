"""MCP launcher for Konnect — portable across Windows, macOS, and Linux.

Wraps the binary so that paths containing spaces are passed as a single argv
entry, the KiCad IPC socket has a sane default, and the configured symbol
library is exported. Stdlib only: this runs as an MCP stdio server entry point.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILENAMES = ("kicad-cursor.yaml", ".kicad-cursor.yaml")


def konnectBinary() -> Path:
    name = "konnect.exe" if sys.platform == "win32" else "konnect"
    return REPO_ROOT / "bin" / name


def defaultSocketUri() -> str:
    socketPath = Path(tempfile.gettempdir()) / "kicad" / "api.sock"
    return f"ipc://{socketPath}"


def symbolLibraryFromConfig() -> str | None:
    """Read symbolLibrary.path without a yaml dependency."""
    for name in CONFIG_FILENAMES:
        configPath = REPO_ROOT / name
        if not configPath.is_file():
            continue
        inSymbolLibrary = False
        for line in configPath.read_text(encoding="utf-8").splitlines():
            if re.match(r"^\s*symbolLibrary:\s*$", line):
                inSymbolLibrary = True
                continue
            if inSymbolLibrary:
                match = re.match(r"^\s*path:\s*(.+)$", line)
                if match:
                    return match.group(1).strip().strip("\"'")
                if re.match(r"^\S", line):
                    break
    return os.environ.get("KICAD_SYMBOL_LIBRARY")


def buildEnvironment() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("KICAD_API_SOCKET", defaultSocketUri())

    # Konnect ignores sym-lib-table on some paths (mixelpixx/Konnect#105);
    # point KICAD10_SYMBOL_DIR at the configured library so symbols resolve by name.
    symbolLibrary = symbolLibraryFromConfig()
    if symbolLibrary and (Path(symbolLibrary) / "global.kicad_sym").is_file():
        env["KICAD10_SYMBOL_DIR"] = symbolLibrary
    return env


def main() -> int:
    exe = konnectBinary()
    if not exe.is_file():
        print(
            f"Konnect not found at {exe}. Run: python scripts/install_konnect.py",
            file=sys.stderr,
        )
        return 1

    return subprocess.run([str(exe), *sys.argv[1:]], env=buildEnvironment(), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
