"""CLI sub-command: split — split a log file into smaller chunks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.splitter import split_by_lines, split_by_size, split_by_time, write_chunks


def add_splitter_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("split", help="Split a log file into smaller chunks")
    p.add_argument("file", help="Input log file")
    p.add_argument(
        "--mode",
        choices=["lines", "size", "time"],
        default="lines",
        help="Splitting strategy (default: lines)",
    )
    p.add_argument(
        "--chunk-lines",
        type=int,
        default=500,
        metavar="N",
        help="Lines per chunk when mode=lines (default: 500)",
    )
    p.add_argument(
        "--chunk-bytes",
        type=int,
        default=1_048_576,
        metavar="BYTES",
        help="Max bytes per chunk when mode=size (default: 1 MiB)",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Time interval per chunk in minutes when mode=time (default: 60)",
    )
    p.add_argument(
        "--output-dir",
        default="split_output",
        metavar="DIR",
        help="Directory to write chunk files (default: split_output)",
    )
    p.add_argument(
        "--stem",
        default="chunk",
        help="Filename stem for chunk files (default: chunk)",
    )
    p.set_defaults(func=run_splitter)


def run_splitter(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text().splitlines(keepends=True)

    if args.mode == "lines":
        result = split_by_lines(lines, args.chunk_lines)
    elif args.mode == "size":
        result = split_by_size(lines, args.chunk_bytes)
    else:
        result = split_by_time(lines, args.interval)

    written = write_chunks(result, args.output_dir, stem=args.stem)
    print(
        f"Split {result.source_lines} lines into {result.chunk_count} chunk(s) "
        f"[mode={result.mode}] → {args.output_dir}/"
    )
    for p in written:
        print(f"  {p}")
