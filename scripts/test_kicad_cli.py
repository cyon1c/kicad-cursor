"""Run kicad-cli ERC/DRC against a project (no IPC required)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from kicad_cursor_config import addProjectArgs, findProjectFiles, resolveKicadCli, resolveProjectDir


def runCli(kicadCli: Path, args: list[str]) -> int:
    cmd = [str(kicadCli), *args]
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    addProjectArgs(parser)
    parser.add_argument("--erc-only", action="store_true")
    parser.add_argument("--drc-only", action="store_true")
    args = parser.parse_args()

    try:
        projectDir = resolveProjectDir(args.project_dir, args.project)
        kicadCli = resolveKicadCli()
        sch, pcb, _ = findProjectFiles(projectDir)
    except (FileNotFoundError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2

    runErc = not args.drc_only
    runDrc = not args.erc_only

    if runErc and not sch.is_file():
        print(f"FAIL: schematic missing: {sch}", file=sys.stderr)
        return 2
    if runDrc and not pcb.is_file():
        print(f"FAIL: pcb missing: {pcb}", file=sys.stderr)
        return 2

    ercCode = 0
    drcCode = 0

    if runErc:
        print("=== ERC (schematic) ===")
        ercCode = runCli(kicadCli, ["sch", "erc", str(sch)])

    if runDrc:
        print("=== DRC (pcb) ===")
        drcCode = runCli(kicadCli, ["pcb", "drc", str(pcb)])

    if ercCode == 0 and drcCode == 0:
        print("\nOK: checks completed")
    else:
        print(f"\nNOTE: ERC exit={ercCode}, DRC exit={drcCode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
