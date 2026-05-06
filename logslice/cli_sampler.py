"""CLI sub-command: sample — thin out large log files before processing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from logslice.sampler import sample_every_n, sample_head, sample_random


def add_sampler_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "sample",
        help="Thin out a log file by keeping every N-th line, a random fraction, or the first N lines.",
    )
    p.add_argument("file", help="Path to the log file")

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--every",
        metavar="N",
        type=int,
        help="Keep every N-th line",
    )
    mode.add_argument(
        "--fraction",
        metavar="F",
        type=float,
        help="Keep each line with probability F (0 < F <= 1)",
    )
    mode.add_argument(
        "--head",
        metavar="N",
        type=int,
        help="Keep only the first N lines",
    )

    p.add_argument("--seed", type=int, default=None, help="Random seed (for --fraction)")
    p.add_argument("--output", "-o", default=None, help="Write sampled lines to file instead of stdout")
    p.set_defaults(func=run_sampler)


def run_sampler(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    raw_lines: List[str] = path.read_text(encoding="utf-8").splitlines(keepends=True)

    if args.every is not None:
        result = sample_every_n(raw_lines, args.every)
    elif args.fraction is not None:
        result = sample_random(raw_lines, args.fraction, seed=args.seed)
    else:
        result = sample_head(raw_lines, args.head)

    output_text = "".join(result.lines)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(
            f"Sampled {result.total_output}/{result.total_input} lines "
            f"({result.ratio:.1%}) → {args.output}"
        )
    else:
        sys.stdout.write(output_text)
        print(
            f"\n# Sampled {result.total_output}/{result.total_input} lines ({result.ratio:.1%})",
            file=sys.stderr,
        )
