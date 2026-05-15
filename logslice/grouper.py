"""Group log lines by a regex capture pattern or by time window."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from logslice.profiler import _parse_ts


@dataclass
class GroupResult:
    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    @property
    def group_count(self) -> int:
        return len(self.groups)


def group_by_pattern(lines: List[str], pattern: str, label: str = "group") -> GroupResult:
    """Group lines by a named or unnamed capture group in *pattern*.

    The first capture group is used as the bucket key.  Lines that do not
    match are collected in ``ungrouped``.
    """
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid grouping pattern: {exc}") from exc

    groups: Dict[str, List[str]] = defaultdict(list)
    ungrouped: List[str] = []

    for line in lines:
        m = rx.search(line)
        if m:
            key = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            groups[key].append(line)
        else:
            ungrouped.append(line)

    return GroupResult(groups=dict(groups), ungrouped=ungrouped)


def group_by_window(lines: List[str], window_seconds: int = 60) -> GroupResult:
    """Group lines into fixed-width time windows.

    Lines whose timestamp cannot be parsed are placed in ``ungrouped``.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be a positive integer")

    groups: Dict[str, List[str]] = defaultdict(list)
    ungrouped: List[str] = []

    for line in lines:
        ts: Optional[datetime] = _parse_ts(line)
        if ts is None:
            ungrouped.append(line)
            continue
        bucket = int(ts.timestamp() // window_seconds) * window_seconds
        key = datetime.utcfromtimestamp(bucket).strftime("%Y-%m-%dT%H:%M:%SZ")
        groups[key].append(line)

    return GroupResult(groups=dict(groups), ungrouped=ungrouped)
