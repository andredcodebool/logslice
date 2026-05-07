"""CLI sub-command for log line normalization."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.normalizer import normalize_lines, _BUILTIN


def add_normalizer_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "normalize",
        help="Replace noisy fields (timestamps, IPs, UUIDs, …) with placeholders.",
    )
    p.add_argument("file", help="Log file to normalize")
    p.add_argument(
        "--rules",
        nargs="+",
        default=[],
        metavar="RULE",
        help=f"Built-in rules to apply: {list(_BUILTIN)}",
    )
    p.add_argument(
        "--custom",
        nargs="+",
        default=[],
        metavar="PATTERN=REPLACEMENT",
        help="Custom substitution rules as 'pattern=replacement' pairs.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print summary statistics after normalization.",
    )
    p.add_argument(
        "--inplace",
        action="store_true",
        help="Overwrite the input file with normalized output.",
    )
    p.set_defaults(func=run_normalizer)


def run_normalizer(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    try:
        result = normalize_lines(
            lines,
            builtin_rules=args.rules,
            custom_rules=args.custom,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    output = "".join(result.normalized_lines)

    if args.inplace:
        path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    if args.stats:
        print(
            f"\n--- normalize stats ---",
            file=sys.stderr,
        )
        print(f"  total lines   : {result.total}", file=sys.stderr)
        print(f"  changed lines : {result.changed_count}", file=sys.stderr)
        print(f"  rules applied : {', '.join(result.rules_applied) or 'none'}", file=sys.stderr)
