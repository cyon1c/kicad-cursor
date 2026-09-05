"""Download the Konnect MCP server binary for the current platform.

Stdlib only — runs before `uv sync` and on a bare Python 3.11+.

    python scripts/install_konnect.py [--version v0.11.0] [--force]
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "bin"
DEFAULT_VERSION = "v0.11.0"
RELEASE_URL = "https://github.com/mixelpixx/Konnect/releases/download"

# (system, machine) → release asset target triple
ASSET_TARGETS = {
    ("windows", "amd64"): "x86_64-pc-windows-msvc",
    ("windows", "x86_64"): "x86_64-pc-windows-msvc",
    ("darwin", "arm64"): "aarch64-apple-darwin",
    ("darwin", "x86_64"): "x86_64-apple-darwin",
    ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
    ("linux", "amd64"): "x86_64-unknown-linux-gnu",
}


def binaryName() -> str:
    return "konnect.exe" if sys.platform == "win32" else "konnect"


def resolveTarget() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    target = ASSET_TARGETS.get((system, machine))
    if target:
        return target
    raise RuntimeError(
        f"No Konnect release for {system}/{machine}. "
        "Build from source: https://github.com/mixelpixx/Konnect"
    )


def assetName(version: str, target: str) -> str:
    extension = "zip" if "windows" in target else "tar.gz"
    return f"konnect-{version}-{target}.{extension}"


def download(url: str, destination: Path) -> None:
    print(f"Downloading {url}")
    try:
        with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Download failed ({error.code}): {url}") from error


def extract(archive: Path, destination: Path) -> None:
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
        return
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(destination)


def findBinary(searchRoot: Path) -> Path:
    matches = sorted(searchRoot.rglob(binaryName()))
    if not matches:
        raise RuntimeError(f"{binaryName()} not found in the downloaded archive")
    return matches[0]


def install(version: str, force: bool) -> Path:
    target = resolveTarget()
    installed = BIN_DIR / binaryName()
    if installed.is_file() and not force:
        print(f"Already installed: {installed} (use --force to reinstall)")
        return installed

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    asset = assetName(version, target)
    with tempfile.TemporaryDirectory() as workDir:
        work = Path(workDir)
        archive = work / asset
        download(f"{RELEASE_URL}/{version}/{asset}", archive)
        extracted = work / "extracted"
        extract(archive, extracted)
        shutil.copy2(findBinary(extracted), installed)

    installed.chmod(installed.stat().st_mode | 0o755)
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Konnect release tag")
    parser.add_argument("--force", action="store_true", help="Reinstall if already present")
    args = parser.parse_args()

    try:
        installed = install(args.version, args.force)
    except (RuntimeError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Installed: {installed}")
    result = subprocess.run([str(installed), "--version"], check=False)
    if result.returncode != 0:
        print("WARNING: binary did not report a version", file=sys.stderr)
    print("Reload MCP in Cursor to pick up the konnect server.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
