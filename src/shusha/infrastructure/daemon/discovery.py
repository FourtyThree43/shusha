"""
Executable discovery, validation, and capability inspection for aria2c.
"""

import os
import shutil
import subprocess
from pathlib import Path


def validate_executable(path: Path) -> bool:
    """Check if a path exists, is a file, and has execute permissions."""
    return path.is_file() and os.access(path, os.X_OK)


def find_aria2_executable(custom_path: Path | str | None = None) -> Path | None:
    """
    Discover the aria2c binary.
    Precedence:
      1. Explicitly provided custom path
      2. Environment variable ARIA2C_PATH
      3. System PATH lookup
      4. Standard OS installation directories
    """
    # 1. Custom path
    if custom_path:
        p = Path(custom_path).expanduser().resolve()
        if validate_executable(p):
            return p

    # 2. Environment variable
    env_path = os.environ.get("ARIA2C_PATH")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if validate_executable(p):
            return p

    # 3. System PATH
    which_path = shutil.which("aria2c")
    if which_path:
        p = Path(which_path).resolve()
        if validate_executable(p):
            return p

    # 4. Standard platform locations
    candidate_paths = [
        Path("/usr/bin/aria2c"),
        Path("/usr/local/bin/aria2c"),
        Path("/opt/homebrew/bin/aria2c"),
        Path("/usr/local/opt/aria2/bin/aria2c"),
        Path("C:/Program Files/aria2/aria2c.exe"),
        Path("C:/Program Files (x86)/aria2/aria2c.exe"),
    ]

    for cand in candidate_paths:
        if cand.exists() and validate_executable(cand):
            return cand

    return None


def inspect_aria2_version(executable_path: Path) -> tuple[str, list[str]]:
    """
    Run `aria2c --version` and extract version string and compile-time features.
    """
    if not validate_executable(executable_path):
        raise FileNotFoundError(f"Invalid aria2 executable: '{executable_path}'")

    res = subprocess.run(
        [str(executable_path), "--version"],
        capture_output=True,
        text=True,
        check=True,
        timeout=5.0,
    )

    lines = res.stdout.strip().splitlines()
    version = "unknown"
    features: list[str] = []

    if lines:
        first_line = lines[0]
        if "aria2 version" in first_line:
            version = first_line.split("aria2 version")[-1].strip()

    for line in lines:
        if line.startswith("Enabled Features:"):
            features_str = line.split("Enabled Features:")[-1].strip()
            features = [f.strip() for f in features_str.split(",") if f.strip()]

    return version, features
