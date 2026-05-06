"""Live log file watcher that tails a file and applies slice filters in real time."""

import time
import re
from pathlib import Path
from typing import Optional

from logslice.parser import extract_timestamp, compile_filter, line_matches_filter
from logslice.highlighter import highlight_line


DEFAULT_POLL_INTERVAL = 0.25  # seconds


def tail_file(path: str, poll_interval: float = DEFAULT_POLL_INTERVAL):
    """Generator that yields new lines appended to a file, blocking between polls."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(0, 2)  # seek to end
        while True:
            line = fh.readline()
            if line:
                yield line.rstrip("\n")
            else:
                time.sleep(poll_interval)


def watch(
    path: str,
    pattern: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    colorize: bool = True,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> None:
    """Watch a log file and print matching lines to stdout in real time.

    Args:
        path: Path to the log file.
        pattern: Optional regex filter; only matching lines are shown.
        start: Optional ISO-format start timestamp string (inclusive).
        end: Optional ISO-format end timestamp string (inclusive).
        colorize: Whether to apply ANSI color highlighting.
        poll_interval: Seconds between file polls.
    """
    compiled = compile_filter(pattern)
    start_dt = _parse_optional_dt(start)
    end_dt = _parse_optional_dt(end)

    for line in tail_file(path, poll_interval=poll_interval):
        if not line_matches_filter(line, compiled):
            continue

        if start_dt or end_dt:
            ts = extract_timestamp(line)
            if ts is not None:
                if start_dt and ts < start_dt:
                    continue
                if end_dt and ts > end_dt:
                    continue

        output = highlight_line(line, compiled) if colorize else line
        print(output)


def _parse_optional_dt(value: Optional[str]):
    """Parse an ISO datetime string or return None."""
    if value is None:
        return None
    from datetime import datetime
    return datetime.fromisoformat(value)
