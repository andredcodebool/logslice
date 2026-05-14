"""CLI sub-command: score — rank log lines by relevance."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from logslice.scorer import score_lines


def add_scorer_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Score log lines by relevance and optionally filter by threshold.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--keywords",
        nargs="*",
        default=[],
        metavar="KW",
        help="Extra keywords that boost a line's score.",
    )
    p.add_argument(
        "--keyword-weight",
        type=float,
        default=0.3,
        metavar="W",
        help="Score added per matching keyword (default: 0.3).",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        metavar="T",
        help="Only output lines with score >= T (default: 0.0 = all).",
    )
    p.add_argument(
        "--show-score",
        action="store_true",
        help="Prefix each output line with its score.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N highest-scored lines.",
    )
    p.set_defaults(func=run_scorer)


def run_scorer(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result = score_lines(
        lines,
        keywords=args.keywords or [],
        keyword_weight=args.keyword_weight,
        threshold=args.threshold,
    )

    filtered = result.above_threshold
    if args.top is not None:
        filtered = sorted(filtered, key=lambda sl: sl.score, reverse=True)[: args.top]

    for sl in filtered:
        if args.show_score:
            print(f"[{sl.score:.4f}] {sl.line}")
        else:
            print(sl.line)

    print(
        f"\n# scored {result.total} lines — "
        f"{len(result.above_threshold)} at or above threshold {args.threshold}",
        file=sys.stderr,
    )
