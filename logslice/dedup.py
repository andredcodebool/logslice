"""Deduplication utilities for log lines."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

# Tokens that vary per-line and should be ignored when comparing "sameness"
_NOISE_PATTERNS = [
    re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b'),  # timestamps
    re.compile(r'\b(?:[0-9a-fA-F]{8}-){3}[0-9a-fA-F]{12}\b'),  # UUIDs
    re.compile(r'\b0x[0-9a-fA-F]+\b'),  # hex numbers
    re.compile(r'\b\d+\b'),  # plain integers
]


def _normalise(line: str) -> str:
    """Strip variable tokens so structurally identical lines compare equal."""
    text = line
    for pat in _NOISE_PATTERNS:
        text = pat.sub('<X>', text)
    return text.strip()


@dataclass
class DedupResult:
    unique_lines: List[str] = field(default_factory=list)
    duplicate_counts: Counter = field(default_factory=Counter)

    @property
    def total_input(self) -> int:
        return sum(self.duplicate_counts.values())

    @property
    def total_unique(self) -> int:
        return len(self.unique_lines)

    @property
    def removed(self) -> int:
        return self.total_input - self.total_unique


def deduplicate(
    lines: Iterable[str],
    *,
    consecutive_only: bool = False,
) -> DedupResult:
    """Remove duplicate log lines.

    Args:
        lines: Iterable of raw log lines.
        consecutive_only: When True only collapse *adjacent* repeated lines
            (cheaper; useful for sorted logs). When False, deduplicate globally.

    Returns:
        DedupResult with unique lines and occurrence counts.
    """
    result = DedupResult()
    seen: dict[str, int] = {}  # normalised -> index in unique_lines
    prev_key: str | None = None

    for raw in lines:
        key = _normalise(raw)
        result.duplicate_counts[key] += 1

        if consecutive_only:
            if key != prev_key:
                result.unique_lines.append(raw)
            prev_key = key
        else:
            if key not in seen:
                seen[key] = len(result.unique_lines)
                result.unique_lines.append(raw)

    return result


def top_repeated(result: DedupResult, n: int = 10) -> List[Tuple[str, int]]:
    """Return the *n* most-repeated normalised patterns with their counts."""
    return result.duplicate_counts.most_common(n)
