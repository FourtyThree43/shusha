"""Standalone Binary Bundler Script for Shusha 2 (Epic E18-I02).

Builds standalone cross-platform executables using PyInstaller:
- Supports single standalone executable directory (`--onedir`)
- Supports single standalone one-file executable (`--onefile`)
- Bundles aria2c and yt-dlp binary engines if present in PATH.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DIST_DIR = ROOT_DIR / "dist" / "binaries"


def find_helper_binaries() -> list[tuple[str, str]]:
    """Discover local aria2c and yt-dlp executables to bundle."""
    binaries: list[tuple[str, str]] = []

    aria2_path = shutil.which("aria2c")
    if aria2_path:
        binaries.append((aria2_path, "."))

    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        binaries.append((ytdlp_path, "."))

    return binaries


def build_package(mode: str = "onefile", app_target: str = "all") -> int:
    """Invoke PyInstaller to build standalone executable."""
    if not shutil.which("pyinstaller"):
        print("Installing pyinstaller via uv pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], check=False
        )

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    helpers = find_helper_binaries()

    targets: list[tuple[str, str]] = []
    if app_target in ("all", "cli"):
        targets.append(
            ("shusha", str(SRC_DIR / "shusha" / "interfaces" / "cli" / "main.py"))
        )
    if app_target in ("all", "gui"):
        targets.append(("shusha-gui", str(SRC_DIR / "shusha" / "main.py")))

    for name, entrypoint in targets:
        cmd: list[str] = [
            "pyinstaller",
            "--noconfirm",
            "--clean",
            f"--name={name}",
            f"--distpath={DIST_DIR}",
            f"--workpath={ROOT_DIR / 'build' / 'pyinstaller'}",
            f"--paths={SRC_DIR}",
        ]

        if mode == "onefile":
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        if name == "shusha-gui" and platform.system() == "Windows":
            cmd.append("--noconsole")

        for bin_path, target_dest in helpers:
            sep = ";" if platform.system() == "Windows" else ":"
            cmd.append(f"--add-binary={bin_path}{sep}{target_dest}")

        # Add ttkbootstrap assets
        cmd.append(entrypoint)

        print(f"\n--- Building {name} [{mode}] ---")
        print("Command:", " ".join(cmd))
        code = subprocess.call(cmd)
        if code != 0:
            print(f"Error packaging {name} (exit code {code})", file=sys.stderr)
            return code

    print(f"\n✔ Successfully packaged targets to {DIST_DIR}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Shusha standalone binaries.")
    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir", "both"],
        default="onefile",
        help="Packaging output mode (onefile single binary, onedir folder, or both)",
    )
    parser.add_argument(
        "--target",
        choices=["all", "cli", "gui"],
        default="all",
        help="Build targets (CLI/TUI, Desktop GUI, or both)",
    )
    args = parser.parse_args()

    if args.mode == "both":
        res = build_package("onefile", args.target)
        if res != 0:
            sys.exit(res)
        res = build_package("onedir", args.target)
        sys.exit(res)
    else:
        sys.exit(build_package(args.mode, args.target))


if __name__ == "__main__":
    main()
