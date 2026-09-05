"""Resolve kicad-cursor paths from config, env vars, and CLI flags."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILENAMES = ("kicad-cursor.yaml", ".kicad-cursor.yaml")
KICAD_CLI_CANDIDATES_BY_PLATFORM = {
    "win32": (
        Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"),
        Path("C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"),
    ),
    "darwin": (
        Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        Path("/Applications/KiCad.app/Contents/MacOS/kicad-cli"),
        Path.home() / "Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    ),
}
KICAD_CLI_CANDIDATES_POSIX = (
    Path("/usr/bin/kicad-cli"),
    Path("/usr/local/bin/kicad-cli"),
    Path("/snap/bin/kicad.kicad-cli"),
    Path("/var/lib/flatpak/exports/bin/org.kicad.KiCad"),
)


def kicadCliCandidates() -> tuple[Path, ...]:
    if sys.platform == "win32":
        return KICAD_CLI_CANDIDATES_BY_PLATFORM["win32"]
    if sys.platform == "darwin":
        return KICAD_CLI_CANDIDATES_BY_PLATFORM["darwin"]
    return KICAD_CLI_CANDIDATES_POSIX


def loadConfig() -> dict:
    for name in CONFIG_FILENAMES:
        path = REPO_ROOT / name
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    return {}


def resolveProjectDir(cliPath: Optional[Path] = None) -> Path:
    if cliPath is not None:
        directory = cliPath.expanduser().resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"KiCad project directory not found: {directory}")
        return directory

    envPath = os.environ.get("KICAD_PROJECT_DIR")
    if envPath:
        directory = Path(envPath).expanduser().resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"KICAD_PROJECT_DIR is not a directory: {directory}")
        return directory

    configPath = loadConfig().get("projectDir")
    if configPath:
        directory = Path(str(configPath)).expanduser().resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"projectDir in kicad-cursor.yaml is not a directory: {directory}")
        return directory

    raise ValueError(
        "No KiCad project configured. Copy kicad-cursor.yaml.example to kicad-cursor.yaml "
        "and set projectDir, or pass --project-dir, or set KICAD_PROJECT_DIR."
    )


def resolveSymbolLibraryBase(cliPath: Optional[Path] = None) -> Path:
    if cliPath is not None:
        return cliPath.expanduser().resolve()

    envPath = os.environ.get("KICAD_SYMBOL_LIBRARY")
    if envPath:
        return Path(envPath).expanduser().resolve()

    config = loadConfig()
    symbolLibrary = config.get("symbolLibrary")
    if isinstance(symbolLibrary, dict) and symbolLibrary.get("path"):
        return Path(str(symbolLibrary["path"])).expanduser().resolve()
    if config.get("symbolLibraryPath"):
        return Path(str(config["symbolLibraryPath"])).expanduser().resolve()

    raise ValueError(
        "No symbol library configured. Set symbolLibrary.path in kicad-cursor.yaml "
        "or pass --symbol-library, or set KICAD_SYMBOL_LIBRARY."
    )


def resolveSymbolLibraryNickname() -> str:
    symbolLibrary = loadConfig().get("symbolLibrary")
    if isinstance(symbolLibrary, dict) and symbolLibrary.get("nickname"):
        return str(symbolLibrary["nickname"])
    return "global"


def resolveKicadCli(cliPath: Optional[Path] = None) -> Path:
    if cliPath is not None:
        path = cliPath.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"kicad-cli not found: {path}")
        return path

    envPath = os.environ.get("KICAD_CLI")
    if envPath:
        path = Path(envPath).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"KICAD_CLI is not a file: {path}")
        return path

    configPath = loadConfig().get("kicadCli")
    if configPath:
        path = Path(str(configPath)).expanduser().resolve()
        if path.is_file():
            return path

    onPath = shutil.which("kicad-cli")
    if onPath:
        return Path(onPath).resolve()

    for candidate in kicadCliCandidates():
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "kicad-cli not found on PATH or in the default KiCad location for this platform. "
        "Install KiCad 10 or set kicadCli in kicad-cursor.yaml."
    )


def findProjectFiles(projectDir: Path) -> tuple[Path, Path, str]:
    proFiles = sorted(projectDir.glob("*.kicad_pro"))
    if not proFiles:
        raise FileNotFoundError(f"No .kicad_pro file in {projectDir}")
    if len(proFiles) > 1:
        names = ", ".join(path.name for path in proFiles)
        raise ValueError(f"Multiple .kicad_pro files in {projectDir}: {names}")

    projectFile = proFiles[0]
    projectName = projectFile.stem
    schematic = projectFile.with_suffix(".kicad_sch")
    pcb = projectFile.with_suffix(".kicad_pcb")
    return schematic, pcb, projectName


def projectDatasheetsDir(projectDir: Path) -> Path:
    return projectDir / "datasheets"
