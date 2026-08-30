"""
CLI Argument Parser definition for Shusha (Epic E13).
Configures all top-level flags and subcommands.
"""

from __future__ import annotations

import argparse
from importlib.metadata import version as get_pkg_version
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser and subcommands."""
    try:
        ver_str = get_pkg_version("shusha")
    except Exception:
        ver_str = "2.0.0-dev"

    parser = argparse.ArgumentParser(
        prog="shusha",
        description="Shusha 2 — Multi-backend download acquisition and orchestration platform",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"Shusha {ver_str}"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "jsonl"],
        default="table",
        help="Global output serialization format (default: table)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Shorthand for --format json (machine-readable output)",
    )
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Shorthand for --format jsonl (line-delimited streaming JSON)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the desktop graphical user interface",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the terminal user interface",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. GUI
    subparsers.add_parser("gui", help="Launch the Shusha desktop graphical interface")

    # 1b. TUI
    subparsers.add_parser("tui", help="Launch the Shusha terminal user interface (TUI)")

    # 2. Daemon Management
    daemon_parser = subparsers.add_parser(
        "daemon", help="Manage background download daemon supervisor"
    )
    daemon_sub = daemon_parser.add_subparsers(dest="daemon_action", required=True)
    daemon_sub.add_parser("start", help="Start local daemon")
    daemon_sub.add_parser("stop", help="Stop local daemon")
    daemon_sub.add_parser("restart", help="Restart local daemon")
    daemon_sub.add_parser("status", help="Check daemon health and responsiveness")

    # 3. Add Downloads / Jobs
    add_parser = subparsers.add_parser(
        "add", help="Add new download tasks (URIs, torrents, metalinks, media)"
    )
    add_parser.add_argument(
        "uris", nargs="*", help="Download URIs, magnet links, or media URLs"
    )
    add_parser.add_argument("--torrent", "-t", type=Path, help="Path to .torrent file")
    add_parser.add_argument(
        "--metalink", "-m", type=Path, help="Path to .metalink file"
    )
    add_parser.add_argument(
        "--dir", "-d", type=Path, help="Custom download destination directory"
    )
    add_parser.add_argument("--category", "-c", type=str, help="Category name or ID")
    add_parser.add_argument(
        "--backend",
        "-b",
        type=str,
        help="Preferred backend engine (e.g. aria2, yt-dlp)",
    )
    add_parser.add_argument("--name", "-n", type=str, help="Custom job name")
    add_parser.add_argument(
        "--split", "-s", type=int, help="Number of connections per server"
    )
    add_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    add_parser.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )
    add_parser.add_argument(
        "--jsonl", action="store_true", help="Output result in JSONL format"
    )

    # 4. List Downloads / Jobs
    list_parser = subparsers.add_parser(
        "list", help="List active, queued, paused, completed, or failed downloads"
    )
    list_parser.add_argument(
        "--state",
        choices=["all", "active", "queued", "paused", "completed", "failed", "removed"],
        default="all",
        help="Filter downloads by state",
    )
    list_parser.add_argument("--category", "-c", type=str, help="Filter by category")
    list_parser.add_argument("--backend", "-b", type=str, help="Filter by backend ID")
    list_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of items to return"
    )
    list_parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    list_parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "jsonl"],
        help="Output format (default: table)",
    )
    list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    list_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 5. Status / Details
    status_parser = subparsers.add_parser(
        "status", help="Show detailed status of download job(s)"
    )
    status_parser.add_argument(
        "download_ids", nargs="*", help="Download/Job ID(s) to inspect"
    )
    status_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    status_parser.add_argument(
        "--json", action="store_true", help="Output status in JSON format"
    )
    status_parser.add_argument(
        "--jsonl", action="store_true", help="Output status in JSONL format"
    )

    # 6. Pause Downloads
    pause_parser = subparsers.add_parser("pause", help="Pause active downloads")
    pause_parser.add_argument("download_ids", nargs="*", help="Download IDs to pause")
    pause_parser.add_argument(
        "--all", action="store_true", help="Pause all active downloads"
    )
    pause_parser.add_argument(
        "--force", action="store_true", help="Force pause immediately"
    )
    pause_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    pause_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    pause_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 7. Resume Downloads
    resume_parser = subparsers.add_parser("resume", help="Resume paused downloads")
    resume_parser.add_argument("download_ids", nargs="*", help="Download IDs to resume")
    resume_parser.add_argument(
        "--all", action="store_true", help="Resume all paused downloads"
    )
    resume_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    resume_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    resume_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 8. Cancel Downloads
    cancel_parser = subparsers.add_parser("cancel", help="Cancel in-progress downloads")
    cancel_parser.add_argument("download_ids", nargs="*", help="Download IDs to cancel")
    cancel_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    cancel_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    cancel_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 9. Remove Downloads
    remove_parser = subparsers.add_parser(
        "remove", help="Remove downloads from management"
    )
    remove_parser.add_argument("download_ids", nargs="*", help="Download IDs to remove")
    remove_parser.add_argument(
        "--delete-files",
        "--files",
        dest="delete_files",
        action="store_true",
        help="Delete downloaded files from disk",
    )
    remove_parser.add_argument(
        "--force", action="store_true", help="Force remove immediately"
    )
    remove_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    remove_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    remove_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 10. Retry Downloads
    retry_parser = subparsers.add_parser(
        "retry", help="Retry failed or cancelled downloads"
    )
    retry_parser.add_argument("download_ids", nargs="*", help="Download IDs to retry")
    retry_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    retry_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    retry_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 11. Resolve (Inspection without execution)
    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Inspect and resolve target URL/input without initiating download",
    )
    resolve_parser.add_argument(
        "target", help="URL, magnet link, media link, or file to inspect"
    )
    resolve_parser.add_argument(
        "--backend", "-b", type=str, help="Preferred backend ID override"
    )
    resolve_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    resolve_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    resolve_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 12. Diagnostics / Doctor
    doctor_parser = subparsers.add_parser(
        "doctor", help="Run system diagnostics and verify environment health"
    )
    doctor_parser.add_argument(
        "--no-backends",
        dest="include_backends",
        action="store_false",
        default=True,
        help="Exclude backend probe diagnostics",
    )
    doctor_parser.add_argument(
        "--no-plugins",
        dest="include_plugins",
        action="store_false",
        default=True,
        help="Exclude plugin diagnostics",
    )
    doctor_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    doctor_parser.add_argument(
        "--json", action="store_true", help="Output diagnostics in JSON format"
    )
    doctor_parser.add_argument(
        "--jsonl", action="store_true", help="Output diagnostics in JSONL format"
    )

    subparsers.add_parser(
        "diagnostics",
        parents=[doctor_parser],
        add_help=False,
        help="Alias for doctor",
    )

    # 13. Checksum Calculation
    hash_parser = subparsers.add_parser(
        "hash", help="Compute cryptographic checksums of a local file"
    )
    hash_parser.add_argument("file", type=Path, help="Path to local file")
    hash_parser.add_argument("--format", "-f", choices=["table", "json", "jsonl"])
    hash_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    hash_parser.add_argument(
        "--jsonl", action="store_true", help="Output in JSONL format"
    )

    # 14. Desktop Entry Installation
    subparsers.add_parser(
        "install-desktop",
        help="Install Linux FreeDesktop .desktop launcher and MIME associations",
    )

    # 15. Browser Native Messaging Host Installation
    host_parser = subparsers.add_parser(
        "install-host",
        help="Register browser native messaging manifests for Chrome/Firefox/Edge/Brave",
    )
    host_parser.add_argument(
        "--dry-run", action="store_true", help="Print manifest without writing to disk"
    )

    # 16. Self-Update / Version Checker
    subparsers.add_parser(
        "update",
        help="Check and install the latest Shusha release from GitHub",
    )

    return parser
