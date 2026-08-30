"""
Modern CLI implementation for Shusha 2 (Epic E13).
Delegates argument parsing and execution to `shusha.interfaces.cli`.
"""

from __future__ import annotations

import argparse

from shusha.interfaces.cli import (
    CliContext,
    CliFormatter,
    OutputFormat,
    build_cli_context,
    build_parser,
    main,
)
from shusha.interfaces.cli.dispatcher import handle_cli as _dispatch_cli
from shusha.main import build_app_context, run_gui, setup_logging


def handle_cli(
    args: argparse.Namespace,
    cli_context: CliContext | None = None,
) -> int:
    """Execute command based on parsed CLI arguments and buses."""
    if cli_context is None:
        try:
            app_ctx = build_app_context()
        except Exception:
            app_ctx = None
        cli_context = build_cli_context(app_context=app_ctx)
    return _dispatch_cli(args, cli_context=cli_context)


__all__ = [
    "CliContext",
    "CliFormatter",
    "OutputFormat",
    "build_app_context",
    "build_cli_context",
    "build_parser",
    "handle_cli",
    "main",
    "run_gui",
    "setup_logging",
]

if __name__ == "__main__":
    main()
