"""
CLI Command and Query Dispatcher (Epic E13).
Routes parsed CLI actions strictly through CommandBus and QueryBus.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any

from shusha.application.commands import (
    CancelJobCommand,
    CreateJobCommand,
    PauseJobCommand,
    RemoveJobCommand,
    ResumeJobCommand,
    RetryJobCommand,
)
from shusha.application.queries import (
    GetDiagnosticsQuery,
    GetJobQuery,
    ListJobsQuery,
    ResolveAcquisitionQuery,
)
from shusha.application.services.post_action_service import PostActionService
from shusha.domain.identifiers import (
    CategoryId,
    make_backend_id,
    make_category_id,
    make_job_id,
)
from shusha.domain.job import Job
from shusha.domain.states import DownloadState
from shusha.infrastructure.os_integration.desktop_entry import install_desktop_entry
from shusha.interfaces.cli.context import CliContext, build_cli_context
from shusha.interfaces.cli.formatter import CliFormatter, OutputFormat, job_to_dict
from shusha.main import build_app_context, run_gui, setup_logging


def resolve_output_format(args: argparse.Namespace) -> OutputFormat:
    """Determine effective output format from command or global arguments."""
    if getattr(args, "jsonl", False):
        return OutputFormat.JSONL
    if getattr(args, "json", False):
        return OutputFormat.JSON
    fmt_str = getattr(args, "format", None)
    if fmt_str:
        try:
            return OutputFormat(fmt_str)
        except ValueError:
            pass
    return OutputFormat.TABLE


def is_display_available() -> bool:
    """Check if a graphical display server is available."""
    import os
    import platform

    system = platform.system()
    if system == "Linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if system in ("Darwin", "Windows"):
        return not (os.environ.get("CI") and not os.environ.get("DISPLAY"))
    return False


def handle_cli(
    args: argparse.Namespace,
    cli_context: CliContext | None = None,
) -> int:
    """Execute command based on parsed CLI arguments and buses."""
    setup_logging(debug=getattr(args, "debug", False))

    # 1. Explicit GUI request
    if getattr(args, "gui", False) or args.command == "gui":
        run_gui()
        return 0

    # 2. Explicit TUI request
    if getattr(args, "tui", False) or args.command == "tui":
        from shusha.interfaces.tui import ShushaTUIApp

        app = ShushaTUIApp()
        app.run()
        return 0

    # 3. Bare invocation: launch GUI if display is available, else fallback to TUI
    if args.command is None:
        if is_display_available():
            try:
                run_gui()
                return 0
            except Exception:
                pass

        from shusha.interfaces.tui import ShushaTUIApp

        app = ShushaTUIApp()
        app.run()
        return 0

    out_fmt = resolve_output_format(args)

    if cli_context is None:
        try:
            app_ctx = build_app_context()
        except Exception:
            app_ctx = None
        cli_context = build_cli_context(app_context=app_ctx)

    command_bus = cli_context.command_bus
    query_bus = cli_context.query_bus
    app_ctx = cli_context.app_context

    # 1. Daemon Management
    if args.command == "daemon":
        if not app_ctx:
            print(
                CliFormatter.format_error(
                    "Application context not available for daemon", out_fmt
                ),
                file=sys.stderr,
            )
            return 1
        supervisor = getattr(app_ctx, "daemon_supervisor", None)
        if not supervisor:
            print(
                CliFormatter.format_error("Daemon supervisor not configured", out_fmt),
                file=sys.stderr,
            )
            return 1

        match args.daemon_action:
            case "start":
                if out_fmt == OutputFormat.TABLE:
                    print("Starting aria2 daemon...")
                success = supervisor.start()
                if success:
                    health = supervisor.get_health()
                    if out_fmt == OutputFormat.TABLE:
                        print(f"✔ aria2 daemon is running (version: {health.version})")
                    else:
                        print(
                            json.dumps(
                                {
                                    "daemon": "started",
                                    "status": health.status.value,
                                    "version": health.version,
                                }
                            )
                        )
                    return 0
                if out_fmt == OutputFormat.TABLE:
                    print("✖ Failed to start aria2 daemon", file=sys.stderr)
                else:
                    print(
                        json.dumps(
                            {
                                "error": "Failed to start aria2 daemon",
                                "status": "failed",
                            }
                        )
                    )
                return 1

            case "stop":
                if out_fmt == OutputFormat.TABLE:
                    print("Stopping aria2 daemon...")
                success = supervisor.stop()
                if success:
                    if out_fmt == OutputFormat.TABLE:
                        print("✔ aria2 daemon stopped")
                    else:
                        print(json.dumps({"daemon": "stopped", "status": "stopped"}))
                    return 0
                if out_fmt == OutputFormat.TABLE:
                    print("✖ Failed to stop aria2 daemon", file=sys.stderr)
                else:
                    print(
                        json.dumps(
                            {"error": "Failed to stop aria2 daemon", "status": "failed"}
                        )
                    )
                return 1

            case "restart":
                if out_fmt == OutputFormat.TABLE:
                    print("Restarting aria2 daemon...")
                success = supervisor.restart()
                if success:
                    if out_fmt == OutputFormat.TABLE:
                        print("✔ aria2 daemon restarted")
                    else:
                        print(json.dumps({"daemon": "restarted", "status": "running"}))
                    return 0
                if out_fmt == OutputFormat.TABLE:
                    print("✖ Failed to restart aria2 daemon", file=sys.stderr)
                else:
                    print(
                        json.dumps(
                            {
                                "error": "Failed to restart aria2 daemon",
                                "status": "failed",
                            }
                        )
                    )
                return 1

            case "status":
                health = supervisor.get_health()
                is_healthy = health.status.value == "HEALTHY"
                if out_fmt == OutputFormat.TABLE:
                    print(f"Daemon Status: {health.status.value}")
                    if health.version:
                        print(f"  Version: {health.version}")
                    if health.latency_ms is not None:
                        print(f"  Latency: {health.latency_ms} ms")
                    if health.error_message:
                        print(f"  Error: {health.error_message}")
                else:
                    data = {
                        "status": health.status.value,
                        "version": health.version,
                        "latency_ms": health.latency_ms,
                        "error": health.error_message,
                    }
                    print(
                        json.dumps(
                            data, indent=2 if out_fmt == OutputFormat.JSON else None
                        )
                    )
                return 0 if is_healthy else 1

    # 2. Add Downloads
    if args.command == "add":
        torrent_bytes = (
            args.torrent.read_bytes()
            if getattr(args, "torrent", None) and args.torrent.exists()
            else None
        )
        metalink_bytes = (
            args.metalink.read_bytes()
            if getattr(args, "metalink", None) and args.metalink.exists()
            else None
        )

        uris: list[str] = list(args.uris) if args.uris else []
        if getattr(args, "torrent", None) and str(args.torrent) not in uris:
            uris.append(str(args.torrent))
        if getattr(args, "metalink", None) and str(args.metalink) not in uris:
            uris.append(str(args.metalink))

        if not uris and not torrent_bytes and not metalink_bytes:
            err_msg = "Must provide at least one URI or a torrent/metalink file."
            print(CliFormatter.format_error(err_msg, out_fmt), file=sys.stderr)
            return 1

        options: dict[str, str] = {}
        if getattr(args, "split", None):
            options["split"] = str(args.split)
        if getattr(args, "dir", None):
            options["dir"] = str(args.dir)

        cat_id = CategoryId(args.category) if getattr(args, "category", None) else None
        backend_id = (
            make_backend_id(args.backend) if getattr(args, "backend", None) else None
        )
        custom_name = getattr(args, "name", None)

        action_results: list[dict[str, Any]] = []
        has_error = False

        for target in uris:
            job_name = custom_name or Path(target).name or target
            cmd = CreateJobCommand(
                name=job_name,
                source_input=target,
                backend_id=backend_id,
                destination_dir=str(args.dir) if getattr(args, "dir", None) else None,
                options=options,
                category_id=cat_id,
            )
            try:
                res = command_bus.dispatch(cmd)
                if isinstance(res, list):
                    for r in res:
                        action_results.append(
                            {"id": str(r), "name": job_name, "status": "queued"}
                        )
                elif isinstance(res, Job):
                    action_results.append(job_to_dict(res))
                else:
                    action_results.append(
                        {"id": str(res), "name": job_name, "status": "queued"}
                    )
            except Exception as e:
                has_error = True
                action_results.append({"id": target, "name": job_name, "error": str(e)})

        formatted = CliFormatter.format_action_results(
            action_results, out_fmt, action_name="Added"
        )
        if has_error and out_fmt == OutputFormat.TABLE:
            print(formatted, file=sys.stderr)
        else:
            print(formatted)
        return 1 if has_error else 0

    # 3. List Downloads
    if args.command == "list":
        st_filter: DownloadState | None = None
        if args.state != "all":
            with contextlib.suppress(ValueError):
                st_filter = DownloadState(args.state.upper())

        cat_filter = (
            make_category_id(args.category) if getattr(args, "category", None) else None
        )
        bid_filter = (
            make_backend_id(args.backend) if getattr(args, "backend", None) else None
        )

        query = ListJobsQuery(
            state=st_filter,
            category_id=cat_filter,
            backend_id=bid_filter,
            limit=getattr(args, "limit", 100),
            offset=getattr(args, "offset", 0),
        )
        try:
            jobs = query_bus.dispatch(query)
            print(CliFormatter.format_jobs(jobs, out_fmt))
            return 0
        except Exception as e:
            print(CliFormatter.format_error(str(e), out_fmt), file=sys.stderr)
            return 1

    # 4. Status
    if args.command == "status":
        ids: list[str] = getattr(args, "download_ids", []) or []
        if not ids:
            # Fall back to listing all jobs
            query = ListJobsQuery()
            jobs = query_bus.dispatch(query)
            print(CliFormatter.format_jobs(jobs, out_fmt))
            return 0

        job_results: list[Any] = []
        missing_ids: list[str] = []
        for jid in ids:
            query = GetJobQuery(job_id=make_job_id(jid))
            job = query_bus.dispatch(query)
            if job is not None:
                job_results.append(job)
            else:
                missing_ids.append(jid)

        if missing_ids and not job_results:
            err_msg = f"Downloads not found: {', '.join(missing_ids)}"
            print(CliFormatter.format_error(err_msg, out_fmt), file=sys.stderr)
            return 1

        if len(job_results) == 1 and not missing_ids:
            print(CliFormatter.format_job_detail(job_results[0], out_fmt))
        else:
            print(CliFormatter.format_jobs(job_results, out_fmt))

        if missing_ids:
            print(
                CliFormatter.format_error(
                    f"Missing IDs: {', '.join(missing_ids)}", out_fmt
                ),
                file=sys.stderr,
            )
            return 1
        return 0

    # 5. Pause
    if args.command == "pause":
        if getattr(args, "all", False):
            if app_ctx and hasattr(app_ctx, "client"):
                app_ctx.client.pause_all(force=getattr(args, "force", False))
                if out_fmt == OutputFormat.TABLE:
                    print("✔ Paused all downloads")
                else:
                    print(json.dumps([{"status": "paused_all"}]))
                return 0
            # Otherwise list active and pause each
            active_jobs = query_bus.dispatch(ListJobsQuery(state=DownloadState.ACTIVE))
            args.download_ids = [
                str(j.id if isinstance(j, Job) else j.download_id) for j in active_jobs
            ]

        if not getattr(args, "download_ids", None):
            print(
                CliFormatter.format_error(
                    "Specify download IDs to pause or use --all", out_fmt
                ),
                file=sys.stderr,
            )
            return 1

        results: list[dict[str, Any]] = []
        has_error = False
        for item in args.download_ids:
            cmd = PauseJobCommand(job_id=make_job_id(item))
            try:
                command_bus.dispatch(cmd)
                results.append({"id": item, "status": "paused", "state": "PAUSED"})
            except Exception as e:
                has_error = True
                results.append({"id": item, "error": str(e)})

        print(
            CliFormatter.format_action_results(results, out_fmt, action_name="Paused")
        )
        return 1 if has_error else 0

    # 6. Resume
    if args.command == "resume":
        if getattr(args, "all", False):
            if app_ctx and hasattr(app_ctx, "client"):
                app_ctx.client.unpause_all()
                if out_fmt == OutputFormat.TABLE:
                    print("✔ Resumed all downloads")
                else:
                    print(json.dumps([{"status": "resumed_all"}]))
                return 0
            paused_jobs = query_bus.dispatch(ListJobsQuery(state=DownloadState.PAUSED))
            args.download_ids = [
                str(j.id if isinstance(j, Job) else j.download_id) for j in paused_jobs
            ]

        if not getattr(args, "download_ids", None):
            print(
                CliFormatter.format_error(
                    "Specify download IDs to resume or use --all", out_fmt
                ),
                file=sys.stderr,
            )
            return 1

        results = []
        has_error = False
        for item in args.download_ids:
            cmd = ResumeJobCommand(job_id=make_job_id(item))
            try:
                command_bus.dispatch(cmd)
                results.append({"id": item, "status": "resumed", "state": "ACTIVE"})
            except Exception as e:
                has_error = True
                results.append({"id": item, "error": str(e)})

        print(
            CliFormatter.format_action_results(results, out_fmt, action_name="Resumed")
        )
        return 1 if has_error else 0

    # 7. Cancel
    if args.command == "cancel":
        if not getattr(args, "download_ids", None):
            print(
                CliFormatter.format_error("Specify download IDs to cancel", out_fmt),
                file=sys.stderr,
            )
            return 1

        results = []
        has_error = False
        for item in args.download_ids:
            cmd = CancelJobCommand(job_id=make_job_id(item))
            try:
                command_bus.dispatch(cmd)
                results.append({"id": item, "status": "cancelled", "state": "REMOVED"})
            except Exception as e:
                has_error = True
                results.append({"id": item, "error": str(e)})

        print(
            CliFormatter.format_action_results(
                results, out_fmt, action_name="Cancelled"
            )
        )
        return 1 if has_error else 0

    # 8. Remove
    if args.command == "remove":
        if not getattr(args, "download_ids", None):
            print(
                CliFormatter.format_error("Specify download IDs to remove", out_fmt),
                file=sys.stderr,
            )
            return 1

        del_files = bool(getattr(args, "delete_files", False))
        results = []
        has_error = False
        for item in args.download_ids:
            cmd = RemoveJobCommand(job_id=make_job_id(item), delete_files=del_files)
            try:
                command_bus.dispatch(cmd)
                results.append(
                    {"id": item, "status": "removed", "deleted_files": del_files}
                )
            except Exception as e:
                has_error = True
                results.append({"id": item, "error": str(e)})

        print(
            CliFormatter.format_action_results(results, out_fmt, action_name="Removed")
        )
        return 1 if has_error else 0

    # 9. Retry
    if args.command == "retry":
        if not getattr(args, "download_ids", None):
            print(
                CliFormatter.format_error("Specify download IDs to retry", out_fmt),
                file=sys.stderr,
            )
            return 1

        results = []
        has_error = False
        for item in args.download_ids:
            cmd = RetryJobCommand(job_id=make_job_id(item))
            try:
                job = command_bus.dispatch(cmd)
                results.append({"id": item, "status": "retried", "state": "QUEUED"})
            except Exception as e:
                has_error = True
                results.append({"id": item, "error": str(e)})

        print(
            CliFormatter.format_action_results(results, out_fmt, action_name="Retried")
        )
        return 1 if has_error else 0

    # 10. Resolve (URL / Target Inspection without immediate execution)
    if args.command == "resolve":
        target = args.target
        bid = make_backend_id(args.backend) if getattr(args, "backend", None) else None
        query = ResolveAcquisitionQuery(raw_input=target, preferred_backend=bid)
        try:
            res = query_bus.dispatch(query)
            print(CliFormatter.format_resolution(res, out_fmt))
            return 0 if res.is_resolved else 1
        except Exception as e:
            print(CliFormatter.format_error(str(e), out_fmt), file=sys.stderr)
            return 1

    # 11. Diagnostics / Doctor
    if args.command in ("doctor", "diagnostics"):
        inc_b = getattr(args, "include_backends", True)
        inc_p = getattr(args, "include_plugins", True)
        query = GetDiagnosticsQuery(include_backends=inc_b, include_plugins=inc_p)
        try:
            report = query_bus.dispatch(query)
            print(CliFormatter.format_diagnostics(report, out_fmt))
            return 0
        except Exception as e:
            print(CliFormatter.format_error(str(e), out_fmt), file=sys.stderr)
            return 1

    # 12. Hash
    if args.command == "hash":
        file_path = args.file
        if not file_path.exists():
            print(
                CliFormatter.format_error(f"File not found '{file_path}'", out_fmt),
                file=sys.stderr,
            )
            return 1
        try:
            md5_h = PostActionService.calculate_file_hash(file_path, "md5")
            sha1_h = PostActionService.calculate_file_hash(file_path, "sha1")
            sha256_h = PostActionService.calculate_file_hash(file_path, "sha256")
            if out_fmt == OutputFormat.TABLE:
                print(f"File:   {file_path.name}")
                print(f"MD5:    {md5_h}")
                print(f"SHA1:   {sha1_h}")
                print(f"SHA256: {sha256_h}")
            else:
                data = {
                    "file": file_path.name,
                    "md5": md5_h,
                    "sha1": sha1_h,
                    "sha256": sha256_h,
                }
                print(
                    json.dumps(data, indent=2 if out_fmt == OutputFormat.JSON else None)
                )
            return 0
        except Exception as e:
            print(
                CliFormatter.format_error(f"Error computing hashes: {e}", out_fmt),
                file=sys.stderr,
            )
            return 1

    # 13. Desktop Installation
    if args.command == "install-desktop":
        try:
            path = install_desktop_entry()
            if out_fmt == OutputFormat.TABLE:
                print(f"✔ Installed desktop entry to: {path}")
            else:
                print(json.dumps({"installed_path": str(path), "status": "success"}))
            return 0
        except Exception as e:
            print(
                CliFormatter.format_error(
                    f"Failed to install desktop entry: {e}", out_fmt
                ),
                file=sys.stderr,
            )
            return 1

    # 14. Browser Native Messaging Host Installation
    if args.command == "install-host":
        from shusha.infrastructure.os_integration.browser_host_installer import (
            install_native_messaging_manifests,
        )

        dry_run = getattr(args, "dry_run", False)
        results = install_native_messaging_manifests(dry_run=dry_run)
        if out_fmt == OutputFormat.TABLE:
            for r in results:
                print(r)
        else:
            print(json.dumps({"results": results}))
        return 0

    # 15. Self-Update / Release Check
    if args.command == "update":
        from importlib.metadata import version as get_pkg_version

        try:
            current_ver = get_pkg_version("shusha")
        except Exception:
            current_ver = "2.0.0-dev"

        if out_fmt == OutputFormat.TABLE:
            print(f"Current version: Shusha {current_ver}")
            print("To update to the latest release from source:")
            print(
                "  Linux/macOS: curl -fsSL https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.sh | bash"
            )
            print(
                "  Windows:     irm https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.ps1 | iex"
            )
            print(
                "  uv:          uv pip install --upgrade git+https://github.com/FourtyThree43/shusha.git"
            )
        else:
            print(
                json.dumps(
                    {
                        "current_version": current_ver,
                        "update_command_unix": "curl -fsSL https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.sh | bash",
                        "update_command_windows": "irm https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.ps1 | iex",
                    }
                )
            )
        return 0

    return 0
