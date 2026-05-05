"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.slicer import slice_log
from logslice.parser import compile_filter
from logslice.formatter import SliceResult, format_output, format_jsonl

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.strptime(value, _DATETIME_FORMAT)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid datetime '{value}'. Expected format: YYYY-MM-DDTHH:MM:SS"
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file slicer with time-range and regex filtering.",
    )
    p.add_argument("logfile", help="Path to the log file to slice.")
    p.add_argument("--start", type=_parse_dt, default=None, metavar="DATETIME",
                   help="Start of time range (YYYY-MM-DDTHH:MM:SS).")
    p.add_argument("--end", type=_parse_dt, default=None, metavar="DATETIME",
                   help="End of time range (YYYY-MM-DDTHH:MM:SS).")
    p.add_argument("--filter", dest="pattern", default=None, metavar="REGEX",
                   help="Regex pattern lines must match.")
    p.add_argument("--no-summary", action="store_true",
                   help="Suppress the summary footer.")
    p.add_argument("--jsonl", action="store_true",
                   help="Output matched lines as JSON-Lines.")
    return p


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        compiled = compile_filter(args.pattern)
        lines, matched, total, first_ts, last_ts = slice_log(
            args.logfile,
            start=args.start,
            end=args.end,
            compiled_filter=compiled,
        )
    except FileNotFoundError:
        print(f"logslice: error: file not found: {args.logfile}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1

    result = SliceResult(
        lines=lines,
        matched_count=matched,
        total_count=total,
        start_time=first_ts,
        end_time=last_ts,
    )

    if args.jsonl:
        print(format_jsonl(result))
    else:
        print(format_output(result, show_summary=not args.no_summary))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())
