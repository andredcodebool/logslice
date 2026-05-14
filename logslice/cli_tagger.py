"""CLI subcommand: tag — label log lines with regex-based tags."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.tagger import tag_lines


def add_tagger_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "tag",
        help="Label log lines with user-defined tags based on regex rules.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "-r",
        "--rule",
        dest="rules",
        metavar="LABEL=PATTERN",
        action="append",
        default=[],
        help="Tagging rule in LABEL=PATTERN format (repeatable).",
    )
    p.add_argument(
        "--tagged-only",
        action="store_true",
        default=False,
        help="Only output lines that received at least one tag.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a tag frequency summary after output.",
    )
    p.set_defaults(func=run_tagger)


def run_tagger(args: argparse.Namespace) -> None:
    try:
        with open(args.file, "r", errors="replace") as fh:
            lines = [ln.rstrip("\n") for ln in fh]
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if not args.rules:
        print("error: at least one --rule LABEL=PATTERN is required.", file=sys.stderr)
        sys.exit(1)

    try:
        result = tag_lines(lines, args.rules)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    for ln in result.lines:
        if args.tagged_only and not ln.tags:
            continue
        print(str(ln))

    if args.summary:
        print()
        print("=== Tag Summary ===")
        for tag, count in sorted(result.tag_summary.items()):
            print(f"  {tag}: {count}")
        print(f"  total tagged: {result.tagged_count}/{result.total}")
