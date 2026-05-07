"""CLI sub-command: merge — chronologically merge multiple log files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.merger import merge_logs


def add_merger_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *merge* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "merge",
        help="Merge multiple log files sorted by timestamp.",
        description=(
            "Chronologically merge two or more log files into a single stream. "
            "Lines with no detectable timestamp preserve their original file order."
        ),
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Log files to merge (at least two recommended).",
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        default=None,
        help="Write merged output to FILE instead of stdout.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a per-source line-count summary to stderr after merging.",
    )
    p.set_defaults(func=run_merger)


def run_merger(args: argparse.Namespace) -> None:
    """Entry point for the *merge* sub-command."""
    try:
        result = merge_logs(args.files)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    merged_text = "\n".join(result.lines)
    if result.lines:
        merged_text += "\n"

    if args.output:
        Path(args.output).write_text(merged_text, encoding="utf-8")
        print(f"Merged {result.total} lines → {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(merged_text)

    if args.summary:
        print("\n--- merge summary ---", file=sys.stderr)
        for source, count in sorted(result.source_counts.items()):
            print(f"  {source}: {count} lines", file=sys.stderr)
        print(f"  total : {result.total} lines", file=sys.stderr)
