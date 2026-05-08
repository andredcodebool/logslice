"""Log profiler: analyse line-rate and burst detection across a log file."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"
)


@dataclass
class ProfileResult:
    total_lines: int
    timestamped_lines: int
    duration_seconds: float
    lines_per_second: float
    busiest_window: Tuple[str, int]  # (window_start_str, line_count)
    window_seconds: int
    counts_by_window: Dict[str, int] = field(default_factory=dict)


def _parse_ts(line: str) -> Optional[datetime]:
    m = _TS_RE.search(line)
    if not m:
        return None
    raw = m.group(1).replace("T", " ")
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _window_key(dt: datetime, window_seconds: int) -> str:
    """Truncate *dt* to the nearest *window_seconds* boundary."""
    epoch = int(dt.timestamp())
    bucket = (epoch // window_seconds) * window_seconds
    return datetime.utcfromtimestamp(bucket).strftime("%Y-%m-%d %H:%M:%S")


def profile_lines(lines: List[str], window_seconds: int = 60) -> ProfileResult:
    """Profile *lines* and return a :class:`ProfileResult`."""
    if window_seconds < 1:
        raise ValueError("window_seconds must be >= 1")

    timestamps: List[datetime] = []
    counts: Dict[str, int] = {}

    for line in lines:
        dt = _parse_ts(line)
        if dt is None:
            continue
        timestamps.append(dt)
        key = _window_key(dt, window_seconds)
        counts[key] = counts.get(key, 0) + 1

    total = len(lines)
    ts_count = len(timestamps)

    if ts_count >= 2:
        duration = (timestamps[-1] - timestamps[0]).total_seconds()
        lps = ts_count / duration if duration > 0 else 0.0
    else:
        duration = 0.0
        lps = 0.0

    if counts:
        busiest_key = max(counts, key=lambda k: counts[k])
        busiest = (busiest_key, counts[busiest_key])
    else:
        busiest = ("", 0)

    return ProfileResult(
        total_lines=total,
        timestamped_lines=ts_count,
        duration_seconds=duration,
        lines_per_second=round(lps, 4),
        busiest_window=busiest,
        window_seconds=window_seconds,
        counts_by_window=counts,
    )
