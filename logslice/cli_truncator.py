"""CLI sub-command: truncate — limit output line count."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from logslice.truncator import truncate_lines, _removed


def add_truncator_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "truncate",
        help="Limit the number of lines shown from a log file.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--limit",
        type=int,
        default=100,
        metavar="N",
        help="Maximum number of lines to keep (default: 100).",
    )
    p.add_argument(
        "--mode",
        choices=["head", "tail", "middle"],
        default="head",
        help="Which lines to keep: head (first), tail (last), middle (both ends).",
    )
    p.add_argument(
        "--no-summary",
        action="store_true",
        help="Suppress the summary line.",
    )


def run_truncator(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    lines: List[str] = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result = truncate_lines(lines, limit=args.limit, mode=args.mode)

    for line in result.lines:
        print(line)

    if not args.no_summary:
        removed = _removed(result)
        if removed > 0:
            print(
                f"\n# truncate({result.mode}): showed {result.truncated_count} of "
                f"{result.original_count} lines ({removed} omitted)",
                file=sys.stderr,
            )
