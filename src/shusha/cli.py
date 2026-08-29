"""
Modern CLI implementation for Shusha 2 using Python standard library argparse.
Provides complete management of downloads, daemon lifecycle, diagnostics, and desktop integration.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.metadata import version as get_pkg_version
from pathlib import Path

from shusha.application.services.post_action_service import PostActionService
from shusha.application.use_cases.download_use_cases import AddDownloadRequest
from shusha.domain.identifiers import CategoryId, DownloadId
from shusha.domain.states import DownloadState
from shusha.infrastructure.diagnostics import (
    format_diagnostics_text,
    generate_diagnostics_report,
)
from shusha.infrastructure.os_integration.desktop_entry import install_desktop_entry
from shusha.main import build_app_context, run_gui, setup_logging


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser and subcommands."""
    try:
        ver_str = get_pkg_version("shusha")
    except Exception:
        ver_str = "2.0.0-dev"

    parser = argparse.ArgumentParser(
        prog="shusha",
        description="Shusha 2 — Modern Desktop Download Manager powered by aria2c",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"Shusha {ver_str}"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. GUI
    subparsers.add_parser("gui", help="Launch the Shusha desktop graphical interface")

    # 2. Daemon Management
    daemon_parser = subparsers.add_parser(
        "daemon", help="Manage background aria2c daemon"
    )
    daemon_sub = daemon_parser.add_subparsers(dest="daemon_action", required=True)
    daemon_sub.add_parser("start", help="Start local aria2c daemon")
    daemon_sub.add_parser("stop", help="Stop local aria2c daemon")
    daemon_sub.add_parser("restart", help="Restart local aria2c daemon")
    daemon_sub.add_parser("status", help="Check daemon health and responsiveness")

    # 3. Add Downloads
    add_parser = subparsers.add_parser(
        "add", help="Add new download tasks (URIs, torrents, metalinks)"
    )
    add_parser.add_argument("uris", nargs="*", help="Download URIs or magnet links")
    add_parser.add_argument("--torrent", "-t", type=Path, help="Path to .torrent file")
    add_parser.add_argument(
        "--metalink", "-m", type=Path, help="Path to .metalink file"
    )
    add_parser.add_argument("--dir", "-d", type=Path, help="Custom download directory")
    add_parser.add_argument("--category", "-c", type=str, help="Category name or ID")
    add_parser.add_argument(
        "--split", "-s", type=int, help="Number of connections per server"
    )

    # 4. List Downloads
    list_parser = subparsers.add_parser(
        "list", help="List active and completed downloads"
    )
    list_parser.add_argument(
        "--state",
        choices=["all", "active", "paused", "completed", "failed"],
        default="all",
        help="Filter downloads by state",
    )
    list_parser.add_argument("--category", "-c", type=str, help="Filter by category")
    list_parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    # 5. Pause Downloads
    pause_parser = subparsers.add_parser("pause", help="Pause active downloads")
    pause_parser.add_argument("download_ids", nargs="*", help="Download IDs to pause")
    pause_parser.add_argument(
        "--all", action="store_true", help="Pause all active downloads"
    )
    pause_parser.add_argument(
        "--force", action="store_true", help="Force pause immediately"
    )

    # 6. Resume Downloads
    resume_parser = subparsers.add_parser("resume", help="Resume paused downloads")
    resume_parser.add_argument("download_ids", nargs="*", help="Download IDs to resume")
    resume_parser.add_argument(
        "--all", action="store_true", help="Resume all paused downloads"
    )

    # 7. Remove Downloads
    remove_parser = subparsers.add_parser("remove", help="Remove downloads")
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

    # 8. Checksum Calculation
    hash_parser = subparsers.add_parser(
        "hash", help="Compute cryptographic checksums of a local file"
    )
    hash_parser.add_argument("file", type=Path, help="Path to local file")

    # 9. Diagnostics / Doctor
    doctor_parser = subparsers.add_parser(
        "doctor", help="Run system diagnostics and verify environment health"
    )
    doctor_parser.add_argument(
        "--json", action="store_true", help="Output diagnostics in JSON format"
    )

    # 10. Desktop Entry Installation
    subparsers.add_parser(
        "install-desktop",
        help="Install Linux FreeDesktop .desktop launcher and MIME associations",
    )

    return parser


def handle_cli(args: argparse.Namespace) -> int:
    """Execute command based on parsed CLI arguments."""
    setup_logging(debug=getattr(args, "debug", False))

    if args.command is None or args.command == "gui":
        run_gui()
        return 0

    if args.command == "daemon":
        app_ctx = build_app_context()
        match args.daemon_action:
            case "start":
                print("Starting aria2 daemon...")
                success = app_ctx.daemon_supervisor.start()
                if success:
                    health = app_ctx.daemon_supervisor.get_health()
                    print(f"✔ aria2 daemon is running (version: {health.version})")
                    return 0
                print("✖ Failed to start aria2 daemon", file=sys.stderr)
                return 1
            case "stop":
                print("Stopping aria2 daemon...")
                success = app_ctx.daemon_supervisor.stop()
                if success:
                    print("✔ aria2 daemon stopped")
                    return 0
                print("✖ Failed to stop aria2 daemon", file=sys.stderr)
                return 1
            case "restart":
                print("Restarting aria2 daemon...")
                success = app_ctx.daemon_supervisor.restart()
                if success:
                    print("✔ aria2 daemon restarted")
                    return 0
                print("✖ Failed to restart aria2 daemon", file=sys.stderr)
                return 1
            case "status":
                health = app_ctx.daemon_supervisor.get_health()
                print(f"Daemon Status: {health.status.value}")
                if health.version:
                    print(f"  Version: {health.version}")
                if health.latency_ms is not None:
                    print(f"  Latency: {health.latency_ms} ms")
                if health.error_message:
                    print(f"  Error: {health.error_message}")
                return 0 if health.status.value == "HEALTHY" else 1

    if args.command == "add":
        app_ctx = build_app_context()
        torrent_bytes = (
            args.torrent.read_bytes()
            if args.torrent and args.torrent.exists()
            else None
        )
        metalink_bytes = (
            args.metalink.read_bytes()
            if args.metalink and args.metalink.exists()
            else None
        )

        if not args.uris and not torrent_bytes and not metalink_bytes:
            print(
                "Error: Must provide at least one URI or a torrent/metalink file.",
                file=sys.stderr,
            )
            return 1

        options = {}
        if args.split:
            options["split"] = str(args.split)

        cat_id = CategoryId(args.category) if args.category else None
        req = AddDownloadRequest(
            uris=args.uris if args.uris else None,
            torrent_bytes=torrent_bytes,
            metalink_bytes=metalink_bytes,
            custom_dir=args.dir,
            category_id=cat_id,
            options=options,
        )

        try:
            dl_ids = app_ctx.add_download_uc.execute(req)
            for dl_id in dl_ids:
                print(f"✔ Added download: {dl_id}")
            return 0
        except Exception as e:
            print(f"✖ Failed to add download: {e}", file=sys.stderr)
            return 1

    if args.command == "list":
        app_ctx = build_app_context()
        if args.category:
            downloads = app_ctx.download_repo.list_by_category(
                CategoryId(args.category)
            )
        elif args.state != "all":
            st_enum = DownloadState(args.state.upper())
            downloads = app_ctx.download_repo.list_by_state(st_enum)
        else:
            downloads = app_ctx.download_repo.list_all()

        if args.format == "json":
            data = [
                {
                    "download_id": str(dl.download_id),
                    "gid": str(dl.gid),
                    "name": dl.name,
                    "state": dl.state.value,
                    "completed_bytes": dl.completed_length.bytes,
                    "total_bytes": dl.total_length.bytes if dl.total_length else None,
                    "progress": dl.progress.value,
                    "download_speed": dl.download_speed.bytes_per_sec,
                    "category": str(dl.category_id or ""),
                }
                for dl in downloads
            ]
            print(json.dumps(data, indent=2))
            return 0

        if not downloads:
            print("No downloads found.")
            return 0

        header = f"{'ID':<16} {'NAME':<32} {'PROGRESS':<10} {'SIZE':<20} {'STATE':<12} {'CATEGORY'}"
        print(header)
        print("-" * len(header))
        for dl in downloads:
            size_str = (
                f"{dl.completed_length.human_readable()} / {dl.total_length.human_readable()}"
                if dl.total_length
                else dl.completed_length.human_readable()
            )
            cat_str = str(dl.category_id or "-")
            print(
                f"{dl.download_id!s:<16} {dl.name[:30]:<32} {dl.progress.human_readable():<10} {size_str:<20} {dl.state.value:<12} {cat_str}"
            )
        return 0

    if args.command == "pause":
        app_ctx = build_app_context()
        if args.all:
            app_ctx.client.pause_all(force=args.force)
            print("✔ Paused all downloads")
            return 0
        if not args.download_ids:
            print("Specify download IDs to pause or use --all")
            return 1
        for item in args.download_ids:
            try:
                app_ctx.pause_download_uc.execute(DownloadId(item), force=args.force)
                print(f"✔ Paused download: {item}")
            except Exception as e:
                print(f"✖ Failed to pause {item}: {e}", file=sys.stderr)
        return 0

    if args.command == "resume":
        app_ctx = build_app_context()
        if args.all:
            app_ctx.client.unpause_all()
            print("✔ Resumed all downloads")
            return 0
        if not args.download_ids:
            print("Specify download IDs to resume or use --all")
            return 1
        for item in args.download_ids:
            try:
                app_ctx.resume_download_uc.execute(DownloadId(item))
                print(f"✔ Resumed download: {item}")
            except Exception as e:
                print(f"✖ Failed to resume {item}: {e}", file=sys.stderr)
        return 0

    if args.command == "remove":
        app_ctx = build_app_context()
        if not args.download_ids:
            print("Specify download IDs to remove")
            return 1
        for item in args.download_ids:
            try:
                app_ctx.remove_download_uc.execute(
                    DownloadId(item), delete_files=args.delete_files, force=args.force
                )
                print(f"✔ Removed download: {item}")
            except Exception as e:
                print(f"✖ Failed to remove {item}: {e}", file=sys.stderr)
        return 0

    if args.command == "hash":
        file_path = args.file
        if not file_path.exists():
            print(f"Error: File not found '{file_path}'", file=sys.stderr)
            return 1
        try:
            md5_hash = PostActionService.calculate_file_hash(file_path, "md5")
            sha1_hash = PostActionService.calculate_file_hash(file_path, "sha1")
            sha256_hash = PostActionService.calculate_file_hash(file_path, "sha256")
            print(f"File:   {file_path.name}")
            print(f"MD5:    {md5_hash}")
            print(f"SHA1:   {sha1_hash}")
            print(f"SHA256: {sha256_hash}")
            return 0
        except Exception as e:
            print(f"Error computing hashes: {e}", file=sys.stderr)
            return 1

    if args.command == "doctor":
        app_ctx = build_app_context()
        report = generate_diagnostics_report(
            db_manager=app_ctx.download_repo.db_manager,
            settings_store=app_ctx.settings_store,
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(format_diagnostics_text(report))
        return 0

    if args.command == "install-desktop":
        try:
            path = install_desktop_entry()
            print(f"✔ Installed desktop entry to: {path}")
            return 0
        except Exception as e:
            print(f"✖ Failed to install desktop entry: {e}", file=sys.stderr)
            return 1

    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    code = handle_cli(args)
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
