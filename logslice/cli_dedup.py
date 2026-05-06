"""CLI integration for the deduplication feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.dedup import deduplicate, top_repeated


def add_dedup_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "dedup",
        help="Remove duplicate lines from a log file.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--consecutive",
        action="store_true",
        default=False,
        help="Only collapse consecutive duplicate lines (faster for pre-sorted logs).",
    )
    p.add_argument(
        "--output", "-o",
        default=None,
        help="Write deduplicated lines to this file instead of stdout.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print deduplication statistics to stderr.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show the top N most-repeated patterns in the stats output.",
    )
    p.set_defaults(func=run_dedup)


def run_dedup(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    result = deduplicate(lines, consecutive_only=args.consecutive)

    if args.output:
        Path(args.output).write_text("".join(result.unique_lines), encoding="utf-8")
    else:
        sys.stdout.writelines(result.unique_lines)

    if args.stats:
        print(
            f"\n[dedup] input={result.total_input}  unique={result.total_unique}"
            f"  removed={result.removed}",
            file=sys.stderr,
        )
        if args.top > 0:
            print(f"[dedup] top {args.top} repeated patterns:", file=sys.stderr)
            for pattern, count in top_repeated(result, args.top):
                short = pattern[:80].replace("\n", "")
                print(f"  {count:>6}x  {short}", file=sys.stderr)

    return 0
