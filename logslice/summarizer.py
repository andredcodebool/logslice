"""Summarize a log slice: top patterns, level distribution, time span."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
)
_LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")


@dataclass
class SummaryResult:
    total_lines: int
    level_counts: dict[str, int]
    top_tokens: List[Tuple[str, int]]
    first_timestamp: Optional[str]
    last_timestamp: Optional[str]
    unique_line_ratio: float


def _extract_level(line: str) -> Optional[str]:
    m = _LEVEL_RE.search(line)
    return m.group(1).upper() if m else None


def _extract_timestamp(line: str) -> Optional[str]:
    m = _TIMESTAMP_RE.search(line)
    return m.group(0) if m else None


def summarize(lines: List[str], top_n: int = 10) -> SummaryResult:
    """Compute a summary over a list of log lines."""
    level_counts: Counter = Counter()
    token_counts: Counter = Counter()
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None
    seen: set[str] = set()

    for line in lines:
        lvl = _extract_level(line)
        if lvl:
            level_counts[lvl] += 1

        ts = _extract_timestamp(line)
        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

        for tok in _TOKEN_RE.findall(line):
            token_counts[tok.lower()] += 1

        seen.add(line.rstrip("\n"))

    total = len(lines)
    unique_ratio = len(seen) / total if total else 0.0

    return SummaryResult(
        total_lines=total,
        level_counts=dict(level_counts),
        top_tokens=token_counts.most_common(top_n),
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        unique_line_ratio=round(unique_ratio, 4),
    )


def format_summary(result: SummaryResult) -> str:
    """Render a SummaryResult as a human-readable string."""
    lines = [
        f"Total lines : {result.total_lines}",
        f"Unique ratio: {result.unique_line_ratio:.1%}",
        f"Time span   : {result.first_timestamp or 'n/a'} -> {result.last_timestamp or 'n/a'}",
        "Level counts:",
    ]
    for lvl, cnt in sorted(result.level_counts.items()):
        lines.append(f"  {lvl:<10} {cnt}")
    lines.append(f"Top {len(result.top_tokens)} tokens:")
    for tok, cnt in result.top_tokens:
        lines.append(f"  {tok:<20} {cnt}")
    return "\n".join(lines)
