"""cli_correlator.py – CLI sub-command for log correlation."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.correlator import correlate, format_correlation, group_count, total


def add_correlator_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "correlate",
        help="Group lines from multiple log files by a shared token (e.g. request-id).",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Log files to correlate (use 'label=path' to set a custom label).",
    )
    p.add_argument(
        "--pattern",
        required=True,
        metavar="REGEX",
        help="Regex with a named group 'token', e.g. r'req_id=(?P<token>[\\w-]+)'.",
    )
    p.add_argument(
        "--show-unmatched",
        action="store_true",
        default=False,
        help="Also print lines that contained no token.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print only summary statistics, not individual lines.",
    )
    p.set_defaults(func=run_correlator)


def _open_source(spec: str):
    """Parse 'label=path' or plain 'path'; return (label, file_obj)."""
    if "=" in spec:
        label, _, path = spec.partition("=")
    else:
        label = spec
        path = spec
    return label, open(path, encoding="utf-8", errors="replace")  # noqa: WPS515


def run_correlator(args: argparse.Namespace) -> None:
    sources = []
    handles = []
    for spec in args.files:
        label, fh = _open_source(spec)
        sources.append((label, fh))
        handles.append(fh)

    try:
        result = correlate(sources, args.pattern)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        for fh in handles:
            fh.close()

    if args.summary:
        print(f"groups : {group_count(result)}")
        print(f"total  : {total(result)}")
        print(f"unmatched: {len(result.unmatched)}")
    else:
        output = format_correlation(result, show_unmatched=args.show_unmatched)
        if output:
            print(output)
        print(f"\n-- {group_count(result)} group(s), {total(result)} line(s) total --")
