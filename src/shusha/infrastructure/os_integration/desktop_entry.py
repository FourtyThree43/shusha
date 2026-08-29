"""
Desktop environment integration for Linux / FreeDesktop standards.
Generates and installs .desktop launcher and registers MIME / URL protocol associations.
"""

import contextlib
import os
import subprocess
from pathlib import Path


def generate_desktop_entry(exec_command: str = "shusha") -> str:
    """Generate standard FreeDesktop .desktop specification file content."""
    return f"""[Desktop Entry]
Name=Shusha
GenericName=Download Manager
Comment=High performance desktop download manager powered by aria2c
Exec={exec_command} %U
Icon=shusha
Terminal=false
Type=Application
Categories=Network;FileTransfer;P2P;
MimeType=x-scheme-handler/magnet;application/x-bittorrent;application/metalink+xml;
Keywords=download;manager;aria2;bittorrent;torrent;magnet;metalink;
StartupNotify=true
StartupWMClass=shusha
"""


def install_desktop_entry(
    target_dir: Path | None = None,
    exec_command: str = "shusha",
) -> Path:
    """Install .desktop launcher file to user applications directory."""
    if target_dir is None:
        target_dir = Path.home() / ".local" / "share" / "applications"

    target_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = target_dir / "shusha.desktop"
    desktop_file.write_text(generate_desktop_entry(exec_command), encoding="utf-8")

    # Update desktop database if tool is available
    with (
        open(os.devnull, "w") as devnull,
        contextlib.suppress(Exception),
    ):
        subprocess.run(
            ["update-desktop-database", str(target_dir)],
            stdout=devnull,
            stderr=devnull,
            check=False,
        )

    return desktop_file
