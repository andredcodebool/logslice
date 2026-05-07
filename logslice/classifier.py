"""Classify log lines into severity buckets based on level or pattern matching."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_LEVEL_RE = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.IGNORECASE
)

_SEVERITY_ORDER = ["CRITICAL", "FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]

_NORMALISE = {
    "WARN": "WARNING",
    "FATAL": "CRITICAL",
}


def _extract_level(line: str) -> Optional[str]:
    m = _LEVEL_RE.search(line)
    if not m:
        return None
    raw = m.group(1).upper()
    return _NORMALISE.get(raw, raw)


@dataclass
class ClassifyResult:
    lines: List[str]
    buckets: Dict[str, List[str]] = field(default_factory=dict)
    unclassified: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.lines)

    def count(self, level: str) -> int:
        return len(self.buckets.get(level.upper(), []))

    def dominant_level(self) -> Optional[str]:
        for lvl in _SEVERITY_ORDER:
            if self.buckets.get(lvl):
                return lvl
        return None


def classify_lines(
    lines: List[str],
    extra_patterns: Optional[Dict[str, str]] = None,
) -> ClassifyResult:
    """Classify each line into a severity bucket.

    Args:
        lines: Raw log lines.
        extra_patterns: Optional mapping of label -> regex string for custom buckets.

    Returns:
        ClassifyResult with populated buckets.
    """
    compiled_extras: Dict[str, re.Pattern[str]] = {}
    if extra_patterns:
        for label, pat in extra_patterns.items():
            compiled_extras[label.upper()] = re.compile(pat, re.IGNORECASE)

    buckets: Dict[str, List[str]] = {}
    unclassified: List[str] = []

    for line in lines:
        placed = False
        for label, rx in compiled_extras.items():
            if rx.search(line):
                buckets.setdefault(label, []).append(line)
                placed = True
                break
        if not placed:
            level = _extract_level(line)
            if level:
                buckets.setdefault(level, []).append(line)
            else:
                unclassified.append(line)

    return ClassifyResult(lines=list(lines), buckets=buckets, unclassified=unclassified)
