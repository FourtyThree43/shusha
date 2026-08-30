"""
Main entry point for Shusha CLI (Epic E13).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from shusha.interfaces.cli.dispatcher import handle_cli
from shusha.interfaces.cli.parser import build_parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse command line arguments and dispatch execution."""
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    code = handle_cli(args)
    if code != 0:
        sys.exit(code)


if __name__ == "__main__":
    main()
