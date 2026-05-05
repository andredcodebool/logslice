"""Core log slicing logic: reads a file and yields lines within a time range."""

import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from logslice.parser import compile_filter, extract_timestamp, line_matches_filter


def slice_log(
    filepath: str | Path,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    regex: Optional[str] = None,
    encoding: str = "utf-8",
) -> Iterator[str]:
    """
    Yield log lines from *filepath* that fall within [start, end] and match *regex*.

    Args:
        filepath: Path to the log file.
        start:    Inclusive lower bound for line timestamps (None = no lower bound).
        end:      Inclusive upper bound for line timestamps (None = no upper bound).
        regex:    Optional regular expression to filter lines.
        encoding: File encoding (default utf-8).

    Yields:
        Matching log lines (with newlines stripped).
    """
    compiled_filter = compile_filter(regex)
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Log file not found: {filepath}")

    with filepath.open(encoding=encoding, errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")

            ts = extract_timestamp(line)

            # Apply time bounds only when the line carries a recognisable timestamp
            if ts is not None:
                if start is not None and ts < start:
                    continue
                if end is not None and ts > end:
                    # Log files are typically chronological; stop early
                    break

            if not line_matches_filter(line, compiled_filter):
                continue

            yield line
