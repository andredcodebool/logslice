"""CLI sub-command: group — group log lines by pattern or time window."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.grouper import GroupResult, group_by_pattern, group_by_window


def add_grouper_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("group", help="Group log lines by pattern or time window")
    p.add_argument("file", help="Log file to process")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--pattern",
        metavar="REGEX",
        help="Regex with one capture group used as the bucket key",
    )
    mode.add_argument(
        "--window",
        metavar="SECONDS",
        type=int,
        help="Group by fixed time window (seconds)",
    )
    p.add_argument(
        "--show-ungrouped",
        action="store_true",
        default=False,
        help="Also print lines that could not be grouped",
    )
    p.set_defaults(func=run_grouper)


def run_grouper(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text().splitlines()

    if args.pattern:
        result: GroupResult = group_by_pattern(lines, args.pattern)
    else:
        result = group_by_window(lines, args.window)

    for key, group_lines in sorted(result.groups.items()):
        print(f"=== {key} ({len(group_lines)} lines) ===")
        for line in group_lines:
            print(line)

    if args.show_ungrouped and result.ungrouped:
        print(f"=== (ungrouped: {len(result.ungrouped)} lines) ===")
        for line in result.ungrouped:
            print(line)

    print(
        f"\n[group] {result.group_count} groups, "
        f"{result.total - len(result.ungrouped)} grouped, "
        f"{len(result.ungrouped)} ungrouped"
    )
