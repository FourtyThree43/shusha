"""
Shusha Command Line Interface and Automation package (Epic E13).
Provides modular argument parsing, Bus dispatching, and formatted output.
"""

from shusha.interfaces.cli.context import CliContext, build_cli_context
from shusha.interfaces.cli.dispatcher import handle_cli, resolve_output_format
from shusha.interfaces.cli.formatter import (
    CliFormatter,
    OutputFormat,
    job_to_dict,
    resolution_to_dict,
)
from shusha.interfaces.cli.main import main
from shusha.interfaces.cli.parser import build_parser

__all__ = [
    "CliContext",
    "CliFormatter",
    "OutputFormat",
    "build_cli_context",
    "build_parser",
    "handle_cli",
    "job_to_dict",
    "main",
    "resolution_to_dict",
    "resolve_output_format",
]
