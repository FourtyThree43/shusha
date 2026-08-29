"""Command-Line Interface (CLI) for Shusha Download Manager.

Provides headless commands for managing downloads, daemon lifecycle, torrent creation,
mirror probing, and file hash verification directly from the terminal.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zlib
from pathlib import Path
from typing import Any

from shusha.controller.api import ShushaAPI
from shusha.models.mirror_prober import MirrorProber
from shusha.models.torrent_creator import TorrentCreator


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="shusha",
        description="Shusha Download Manager - Advanced Multi-Protocol CLI & GUI",
    )
    parser.add_argument(
        "--gui", action="store_true", help="Launch Graphical User Interface"
    )
    parser.add_argument("--version", action="store_true", help="Show version info")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. add
    add_p = subparsers.add_parser("add", help="Add new download URL or torrent file")
    add_p.add_argument(
        "url", help="Download URL, Magnet link, or path to .torrent file"
    )
    add_p.add_argument("--out", "-o", help="Target filename")
    add_p.add_argument("--dir", "-d", help="Destination directory")
    add_p.add_argument(
        "--split", "-s", type=int, default=8, help="Number of split connections"
    )
    add_p.add_argument("--header", help="Custom HTTP header (Key: Value)")
    add_p.add_argument("--user-agent", help="Custom User-Agent string")
    add_p.add_argument("--referer", help="Custom Referer URL")

    # 2. list
    list_p = subparsers.add_parser(
        "list", help="List active, waiting, and stopped downloads"
    )
    list_p.add_argument(
        "--status", choices=["active", "waiting", "stopped", "all"], default="all"
    )

    # 3. pause
    pause_p = subparsers.add_parser("pause", help="Pause a download by GID (or all)")
    pause_p.add_argument("gid", nargs="?", default="all", help="Download GID or 'all'")

    # 4. resume
    resume_p = subparsers.add_parser("resume", help="Resume a download by GID (or all)")
    resume_p.add_argument("gid", nargs="?", default="all", help="Download GID or 'all'")

    # 5. remove
    rm_p = subparsers.add_parser("remove", help="Remove a download task")
    rm_p.add_argument("gid", help="Download GID")
    rm_p.add_argument(
        "--files", "-f", action="store_true", help="Delete downloaded files from disk"
    )

    # 6. daemon
    d_p = subparsers.add_parser("daemon", help="Manage aria2 daemon process")
    d_p.add_argument(
        "action", choices=["start", "stop", "restart", "status"], help="Daemon action"
    )

    # 7. stats
    subparsers.add_parser(
        "stats", help="Show global bandwidth and queue transfer statistics"
    )

    # 8. torrent create
    tor_p = subparsers.add_parser("torrent", help="BitTorrent packaging utilities")
    tor_sub = tor_p.add_subparsers(dest="tor_action")
    create_p = tor_sub.add_parser(
        "create", help="Create .torrent file from local file or directory"
    )
    create_p.add_argument("source", help="Source file or folder path")
    create_p.add_argument("--output", "-o", help="Output .torrent file path")
    create_p.add_argument(
        "--piece-size", type=int, default=512 * 1024, help="Piece length in bytes"
    )

    # 9. hash
    hash_p = subparsers.add_parser(
        "hash", help="Compute cryptographic hashes of a file"
    )
    hash_p.add_argument("file", help="File to hash")
    hash_p.add_argument(
        "--algo",
        choices=["md5", "sha1", "sha256", "sha512", "crc32", "all"],
        default="all",
    )

    # 10. probe
    probe_p = subparsers.add_parser("probe", help="Probe and benchmark mirror URLs")
    probe_p.add_argument("urls", nargs="+", help="Mirror URLs to probe")

    return parser


def handle_cli(args: argparse.Namespace) -> int:
    """Execute parsed CLI command."""
    if args.version:
        from shusha.__about__ import __version__

        print(f"Shusha Download Manager v{__version__}")
        return 0

    if not args.subcommand or args.gui:
        # Launch GUI
        from shusha.ShushaDM import main as gui_main

        gui_main()
        return 0

    api = ShushaAPI()

    if args.subcommand == "daemon":
        if args.action == "start":
            pid = api.start_server()
            print(
                f"Daemon started with PID: {pid}" if pid else "Daemon already running."
            )
        elif args.action == "stop":
            api.stop_server()
            print("Daemon stopped.")
        elif args.action == "restart":
            pid = api.restart_server()
            print(f"Daemon restarted (PID: {pid}).")
        elif args.action == "status":
            is_up = api.is_server_running()
            print(f"Aria2 Daemon Status: {'ONLINE' if is_up else 'OFFLINE'}")
        return 0

    if args.subcommand == "add":
        opts: dict[str, Any] = {"split": args.split}
        if args.dir:
            opts["dir"] = args.dir
        if args.out:
            opts["out"] = args.out
        if args.header:
            opts["header"] = args.header
        if args.user_agent:
            opts["user-agent"] = args.user_agent
        if args.referer:
            opts["referer"] = args.referer

        url_target = args.url.strip()
        if url_target.endswith(".torrent") and Path(url_target).is_file():
            dls = api.add_torrent(url_target, options=opts)
            for d in dls:
                print(f"Added Torrent: {d.name or d.gid} [GID: {d.gid}]")
        else:
            dl = api.add_uris([url_target], options=opts)
            if dl:
                print(f"Added Download: {dl.name or dl.gid} [GID: {dl.gid}]")
        return 0

    if args.subcommand == "list":
        downloads = api.get_downloads()
        if not downloads:
            print("No downloads found in queue.")
            return 0
        print(
            f"{'GID':<18} {'STATUS':<12} {'SIZE':<12} {'PROGRESS':<10} {'SPEED':<12} {'NAME'}"
        )
        print("-" * 80)
        for d in downloads:
            print(
                f"{d.gid!s:<18} "
                f"{d.status!s:<12} "
                f"{d.total_length_string():<12} "
                f"{d.progress_string():<10} "
                f"{d.download_speed_string():<12} "
                f"{d.name or 'Unknown'}"
            )
        return 0

    if args.subcommand == "pause":
        if args.gid == "all":
            api.pause_all()
            print("Paused all downloads.")
        else:
            api.pause(args.gid)
            print(f"Paused download {args.gid}.")
        return 0

    if args.subcommand == "resume":
        if args.gid == "all":
            api.resume_all()
            print("Resumed all downloads.")
        else:
            api.resume(args.gid)
            print(f"Resumed download {args.gid}.")
        return 0

    if args.subcommand == "remove":
        api.remove(args.gid, files=args.files)
        print(f"Removed download {args.gid} (files deleted: {args.files}).")
        return 0

    if args.subcommand == "stats":
        stats = api.get_stats()
        print(f"Active Downloads: {stats.num_active}")
        print(f"Waiting Downloads: {stats.num_waiting}")
        print(f"Stopped Downloads: {stats.num_stopped}")
        print(f"Download Speed: {stats.download_speed_string()}")
        print(f"Upload Speed: {stats.upload_speed_string()}")
        return 0

    if args.subcommand == "torrent":
        if args.tor_action == "create":
            out_file, magnet = TorrentCreator.create_torrent_file(
                target_path=args.source,
                output_file=args.output,
                piece_length=args.piece_size,
            )
            print(f"Created Torrent File: {out_file}")
            print(f"Magnet Link: {magnet}")
        return 0

    if args.subcommand == "hash":
        target = Path(args.file)
        if not target.is_file():
            print(f"Error: {target} is not a valid file.", file=sys.stderr)
            return 1
        with open(target, "rb") as f:
            data = f.read()
        print(f"File: {target.name} ({len(data)} bytes)")
        if args.algo in ("md5", "all"):
            print(f"MD5:    {hashlib.md5(data).hexdigest()}")
        if args.algo in ("sha1", "all"):
            print(f"SHA1:   {hashlib.sha1(data).hexdigest()}")
        if args.algo in ("sha256", "all"):
            print(f"SHA256: {hashlib.sha256(data).hexdigest()}")
        if args.algo in ("sha512", "all"):
            print(f"SHA512: {hashlib.sha512(data).hexdigest()}")
        if args.algo in ("crc32", "all"):
            print(f"CRC32:  {zlib.crc32(data) & 0xFFFFFFFF:08X}")
        return 0

    if args.subcommand == "probe":
        print(f"Probing {len(args.urls)} mirror(s)...")
        results = MirrorProber.probe_mirrors(args.urls)
        print(f"{'STATUS':<8} {'LATENCY':<12} {'RANGES':<10} {'SIZE':<12} {'URL'}")
        print("-" * 75)
        for r in results:
            stat_str = "OK" if r.is_alive else "FAIL"
            lat_str = f"{r.latency_ms} ms" if r.is_alive else "TIMEOUT"
            range_str = "YES" if r.supports_ranges else "NO"
            size_str = str(r.content_length) if r.content_length else "N/A"
            print(f"{stat_str:<8} {lat_str:<12} {range_str:<10} {size_str:<12} {r.url}")
        return 0

    return 0


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(handle_cli(args))


if __name__ == "__main__":
    main()
