"""Statistics aggregation for log slices."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)


@dataclass
class LogStats:
    """Aggregated statistics for a set of log lines."""

    total_lines: int = 0
    matched_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None

    @property
    def error_count(self) -> int:
        return self.level_counts.get("ERROR", 0) + self.level_counts.get("CRITICAL", 0) + self.level_counts.get("FATAL", 0)

    @property
    def warning_count(self) -> int:
        return self.level_counts.get("WARNING", 0) + self.level_counts.get("WARN", 0)

    @property
    def match_rate(self) -> Optional[float]:
        """Return the fraction of total lines that were matched, or None if total is zero."""
        if self.total_lines == 0:
            return None
        return self.matched_lines / self.total_lines

    def as_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "match_rate": self.match_rate,
            "level_counts": dict(self.level_counts),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
        }


def extract_level(line: str) -> Optional[str]:
    """Extract the first log level keyword found in a line."""
    match = LEVEL_PATTERN.search(line)
    if match:
        return match.group(0).upper()
    return None


def compute_stats(all_lines: List[str], matched_lines: List[str]) -> LogStats:
    """Compute statistics from all scanned lines and the matched subset."""
    from logslice.parser import extract_timestamp

    stats = LogStats(
        total_lines=len(all_lines),
        matched_lines=len(matched_lines),
    )

    timestamps = []
    for line in matched_lines:
        level = extract_level(line)
        if level:
            stats.level_counts[level] += 1
        ts = extract_timestamp(line)
        if ts:
            timestamps.append(ts)

    if timestamps:
        stats.first_timestamp = str(min(timestamps))
        stats.last_timestamp = str(max(timestamps))

    return stats
