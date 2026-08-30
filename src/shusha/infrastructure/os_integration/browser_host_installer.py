"""Browser Native Messaging Host Installer (Epic E10, E18).

Registers native messaging manifests for Chrome, Chromium, Brave, Edge, and Firefox
so the browser extension can seamlessly communicate with Shusha.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

HOST_NAME = "com.fourtythree43.shusha"
DESCRIPTION = "Shusha Download Acquisition Native Messaging Bridge"


def get_native_host_executable() -> str:
    """Find the path to the shusha-host binary or generate a runner wrapper."""
    which_path = shutil.which("shusha-host")
    if which_path:
        return which_path

    # Fallback to python runner
    return f"{sys.executable} -m shusha.acquisition.browser.bridge"


def build_chrome_manifest(host_path: str) -> dict[str, object]:
    """Generate Chromium / Chrome / Brave / Edge manifest."""
    return {
        "name": HOST_NAME,
        "description": DESCRIPTION,
        "path": host_path,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://*",
        ],
    }


def build_firefox_manifest(host_path: str) -> dict[str, object]:
    """Generate Mozilla Firefox manifest."""
    return {
        "name": HOST_NAME,
        "description": DESCRIPTION,
        "path": host_path,
        "type": "stdio",
        "allowed_extensions": [
            "shusha@fourtythree43.com",
        ],
    }


def get_manifest_directories() -> list[tuple[str, Path]]:
    """Determine standard native messaging manifest directories for the current OS."""
    system = platform.system()
    home = Path.home()
    dirs: list[tuple[str, Path]] = []

    if system == "Linux":
        dirs.extend(
            [
                ("Chrome", home / ".config" / "google-chrome" / "NativeMessagingHosts"),
                ("Chromium", home / ".config" / "chromium" / "NativeMessagingHosts"),
                (
                    "Brave",
                    home
                    / ".config"
                    / "BraveSoftware"
                    / "Brave-Browser"
                    / "NativeMessagingHosts",
                ),
                ("Edge", home / ".config" / "microsoft-edge" / "NativeMessagingHosts"),
                ("Firefox", home / ".mozilla" / "native-messaging-hosts"),
            ]
        )
    elif system == "Darwin":
        app_support = home / "Library" / "Application Support"
        dirs.extend(
            [
                ("Chrome", app_support / "Google" / "Chrome" / "NativeMessagingHosts"),
                ("Chromium", app_support / "Chromium" / "NativeMessagingHosts"),
                (
                    "Brave",
                    app_support
                    / "BraveSoftware"
                    / "Brave-Browser"
                    / "NativeMessagingHosts",
                ),
                ("Edge", app_support / "Microsoft Edge" / "NativeMessagingHosts"),
                ("Firefox", app_support / "Mozilla" / "NativeMessagingHosts"),
            ]
        )
    elif system == "Windows":
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
        )
        dirs.extend(
            [
                (
                    "Chrome",
                    local_app_data
                    / "Google"
                    / "Chrome"
                    / "User Data"
                    / "NativeMessagingHosts",
                ),
                (
                    "Edge",
                    local_app_data
                    / "Microsoft"
                    / "Edge"
                    / "User Data"
                    / "NativeMessagingHosts",
                ),
                (
                    "Firefox",
                    home / "AppData" / "Roaming" / "Mozilla" / "NativeMessagingHosts",
                ),
            ]
        )

    return dirs


def install_native_messaging_manifests(dry_run: bool = False) -> list[str]:
    """Install native messaging JSON manifests across all supported browsers."""
    host_path = get_native_host_executable()
    chrome_manifest = build_chrome_manifest(host_path)
    firefox_manifest = build_firefox_manifest(host_path)

    installed: list[str] = []

    for browser_name, target_dir in get_manifest_directories():
        manifest_data = (
            firefox_manifest if browser_name == "Firefox" else chrome_manifest
        )
        manifest_file = target_dir / f"{HOST_NAME}.json"

        if dry_run:
            installed.append(
                f"[DRY-RUN] Would write to {manifest_file}:\n{json.dumps(manifest_data, indent=2)}"
            )
            continue

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
            installed.append(f"✔ Registered for {browser_name}: {manifest_file}")
        except Exception as e:
            installed.append(f"▲ Skipped {browser_name} ({manifest_file}): {e}")

    return installed
