"""CLI sub-command: annotate — tag log lines that match given patterns."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Tuple

from logslice.annotator import annotate_lines, format_annotations


def add_annotator_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "annotate",
        help="Tag log lines matching regex patterns.",
    )
    p.add_argument("logfile", help="Path to the log file.")
    p.add_argument(
        "--rule",
        metavar=("PATTERN", "TAG"),
        nargs=2,
        action="append",
        dest="rules",
        default=[],
        help="Pattern + tag pair; may be repeated.",
    )
    p.add_argument(
        "--note",
        metavar="NOTE",
        action="append",
        dest="notes",
        default=[],
        help="Optional note for the corresponding --rule (positional).",
    )
    p.add_argument("--no-summary", action="store_true", help="Omit summary line.")
    p.set_defaults(func=run_annotator)


def run_annotator(args: argparse.Namespace) -> None:
    try:
        with open(args.logfile, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        print(f"error: file not found: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    notes: List[Optional[str]] = list(args.notes)
    rules: List[Tuple[str, str, Optional[str]]] = []
    for i, (pattern, tag) in enumerate(args.rules):
        note = notes[i] if i < len(notes) else None
        rules.append((pattern, tag, note))

    if not rules:
        print("warning: no --rule specified; nothing to annotate.", file=sys.stderr)
        return

    result = annotate_lines(lines, rules)
    output = format_annotations(result, show_summary=not args.no_summary)
    if output.strip():
        print(output)
