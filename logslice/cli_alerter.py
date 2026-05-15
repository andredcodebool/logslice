"""CLI sub-command: alert — scan a log file and report rule hits."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from logslice.alerter import AlertResult, build_rules, check_alerts


def add_alerter_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("alert", help="Scan log file for alert rule hits")
    p.add_argument("file", help="Path to log file")
    p.add_argument(
        "-r",
        "--rule",
        dest="rules",
        action="append",
        default=[],
        metavar="LABEL=PATTERN[:LEVEL]",
        help="Alert rule (repeatable)",
    )
    p.add_argument("--summary", action="store_true", help="Print summary only")
    p.add_argument("--exit-code", action="store_true", help="Exit 1 if any hits found")
    p.set_defaults(func=run_alerter)


def run_alerter(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    if not args.rules:
        print("error: at least one --rule is required", file=sys.stderr)
        sys.exit(2)

    try:
        rules = build_rules(args.rules)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    lines: List[str] = path.read_text(encoding="utf-8").splitlines(keepends=True)
    result: AlertResult = check_alerts(lines, rules)

    if not args.summary:
        for hit in result.hits:
            print(str(hit))

    print(
        f"\n--- alert summary: {result.hit_count}/{result.total} lines matched "
        f"({result.hit_rate:.1%}) across {len(result.rules)} rule(s) ---"
    )

    if args.exit_code and result.hit_count > 0:
        sys.exit(1)
