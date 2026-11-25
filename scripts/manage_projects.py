"""List, add, and switch named KiCad project targets in kicad-cursor.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kicad_cursor_config import (
    activeProjectName,
    addProjectTarget,
    defaultConfigFilePath,
    listProjectTargets,
    resolveProjectDir,
    setActiveProject,
)


def cmdList() -> int:
    projects = listProjectTargets()
    active = activeProjectName()
    if not projects:
        print("No project targets configured.")
        print(f"Add one: uv run python scripts/manage_projects.py add <name> <path>")
        return 0

    for name in sorted(projects):
        marker = " *" if name == active else ""
        print(f"{name}{marker}: {projects[name]}")
    if active:
        print(f"\nactive: {active}")
    return 0


def cmdShow() -> int:
    try:
        projectDir = resolveProjectDir()
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    active = activeProjectName()
    if active:
        print(f"active target: {active}")
    print(f"project dir: {projectDir}")
    return 0


def cmdUse(name: str) -> int:
    try:
        configPath = setActiveProject(name)
        projectDir = resolveProjectDir(projectName=name)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"active target: {name}")
    print(f"project dir: {projectDir}")
    print(f"config: {configPath}")
    return 0


def cmdAdd(name: str, projectPath: Path) -> int:
    try:
        configPath = addProjectTarget(name, projectPath)
        projectDir = resolveProjectDir(projectName=name)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"added target: {name}")
    print(f"project dir: {projectDir}")
    print(f"config: {configPath}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List configured project targets")
    subparsers.add_parser("show", help="Show the active project directory")
    useParser = subparsers.add_parser("use", help="Set activeProject in kicad-cursor.yaml")
    useParser.add_argument("name", help="Project target name")
    addParser = subparsers.add_parser("add", help="Add or update a project target")
    addParser.add_argument("name", help="Project target name")
    addParser.add_argument("path", type=Path, help="Path to KiCad project folder")

    args = parser.parse_args()
    if args.command == "list":
        return cmdList()
    if args.command == "show":
        return cmdShow()
    if args.command == "use":
        return cmdUse(args.name)
    if args.command == "add":
        return cmdAdd(args.name, args.path)

    parser.print_help()
    print(f"\nconfig file: {defaultConfigFilePath()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
