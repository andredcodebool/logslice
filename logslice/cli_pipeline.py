"""cli_pipeline.py — CLI subcommand: run a configurable pipeline over a log file."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

from logslice.pipeline import Pipeline, Stage


def add_pipeline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "pipeline",
        help="Apply a chain of transforms (filter, redact-pattern, strip-ansi) to a log file.",
    )
    p.add_argument("file", type=Path, help="Input log file.")
    p.add_argument(
        "--grep",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Keep only lines matching PATTERN (repeatable).",
    )
    p.add_argument(
        "--drop",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Drop lines matching PATTERN (repeatable).",
    )
    p.add_argument(
        "--replace",
        metavar="FROM=TO",
        action="append",
        default=[],
        help="Replace literal string FROM with TO (repeatable).",
    )
    p.add_argument("--stats", action="store_true", help="Print pipeline statistics to stderr.")
    p.set_defaults(func=run_pipeline)


def _make_grep_stage(pattern: str) -> Stage:
    rx = re.compile(pattern)
    return Stage(name=f"grep:{pattern}", transform=lambda line: line if rx.search(line) else None)


def _make_drop_stage(pattern: str) -> Stage:
    rx = re.compile(pattern)
    return Stage(name=f"drop:{pattern}", transform=lambda line: None if rx.search(line) else line)


def _make_replace_stage(spec: str) -> Stage:
    if "=" not in spec:
        raise ValueError(f"--replace requires FROM=TO format, got: {spec!r}")
    from_str, to_str = spec.split("=", 1)
    return Stage(name=f"replace:{from_str}->{to_str}", transform=lambda line: line.replace(from_str, to_str))


def run_pipeline(args: argparse.Namespace) -> None:
    path: Path = args.file
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    pipeline = Pipeline()
    for pat in args.grep:
        pipeline.add_stage(_make_grep_stage(pat))
    for pat in args.drop:
        pipeline.add_stage(_make_drop_stage(pat))
    for spec in args.replace:
        pipeline.add_stage(_make_replace_stage(spec))

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result = pipeline.run(lines)

    for line in result.output:
        print(line)

    if args.stats:
        print(
            f"[pipeline] stages={len(result.stage_names)} "
            f"in={result.lines_in} out={result.lines_out} "
            f"dropped={result.dropped} "
            f"retention={result.retention_rate:.1%}",
            file=sys.stderr,
        )
