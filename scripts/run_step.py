"""Run a cataloged KiCad step by id — single entry point for the agent."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from kicad_cursor_config import REPO_ROOT, addProjectArgs, resolveProjectDir

STEPS_FILE = REPO_ROOT / "steps.yaml"


def loadSteps() -> dict:
    data = yaml.safe_load(STEPS_FILE.read_text(encoding="utf-8"))
    return data


def buildCommand(step: dict, projectDir: Path, extraArgs: dict[str, str]) -> list[str]:
    values = {"project_dir": str(projectDir), **extraArgs}
    tokens: list[str] = []
    for part in step["command"].split():
        if part.startswith("{") and part.endswith("}"):
            key = part[1:-1]
            if key not in values:
                raise KeyError(f"Unknown placeholder {{{key}}} in step command")
            tokens.append(values[key])
        else:
            tokens.append(part)

    return tokens


def listSteps(data: dict) -> None:
    for stepId, step in data["steps"].items():
        print(f"{stepId}: {step['description']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stepId", nargs="?", help="Step id from steps.yaml")
    addProjectArgs(parser)
    parser.add_argument("--lcsc-id", help="LCSC id for fetch-part step")
    parser.add_argument("--pdf", help="PDF path for extract-datasheet step")
    parser.add_argument("--list", action="store_true", help="List available steps")
    args = parser.parse_args()

    data = loadSteps()
    if args.list or not args.stepId:
        listSteps(data)
        return 0

    stepId = args.stepId
    if stepId not in data["steps"]:
        print(f"Unknown step: {stepId}", file=sys.stderr)
        listSteps(data)
        return 2

    step = data["steps"][stepId]

    extraArgs: dict[str, str] = {}
    if "args" in step:
        argValues = {
            "lcsc_id": args.lcsc_id,
            "pdf": args.pdf,
        }
        for argName, rule in step["args"].items():
            value = argValues.get(argName)
            if rule == "required" and not value:
                print(f"Step {stepId} requires --{argName.replace('_', '-')}", file=sys.stderr)
                return 2
            if value:
                extraArgs[argName] = value

    projectDir: Path | None = None
    if "{project_dir}" in step["command"]:
        try:
            projectDir = resolveProjectDir(args.project_dir, args.project)
        except (FileNotFoundError, ValueError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2

    cmd = buildCommand(step, projectDir or Path(), extraArgs)
    print(f"step: {stepId}")
    if projectDir is not None:
        print(f"project: {projectDir}")
    if step.get("requires"):
        print(f"requires: {', '.join(step['requires'])}")

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        return result.returncode

    if step.get("saves") == "remind-user-ctrl-s":
        print("NOTE: Save the board in KiCad (Ctrl+S) to persist to disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
