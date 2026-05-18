"""CLI sub-command: logslice trace — follow a token across log lines."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.tracer import format_trace, trace_lines


def add_tracer_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "trace",
        help="Trace a token (e.g. request-id) across log lines.",
    )
    p.add_argument("file", help="Log file to scan.")
    p.add_argument(
        "--pattern",
        required=True,
        metavar="REGEX",
        help="Regex with one capturing group that extracts the token.",
    )
    p.add_argument(
        "--token",
        default=None,
        metavar="VALUE",
        help="Only show lines for this specific token value.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary line after output.",
    )
    p.set_defaults(func=run_tracer)


def run_tracer(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text(encoding="utf-8").splitlines()
    result = trace_lines(
        lines,
        token_pattern=args.pattern,
        token_filter=args.token,
    )

    output = format_trace(result, show_counts=args.summary)
    if output:
        print(output)
    else:
        print("[trace] no tokens found.", file=sys.stderr)
