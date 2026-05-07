"""Diff two log slices to highlight lines unique to each or common to both."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Sequence

# Strip timestamps and volatile tokens before comparing
_NOISE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?Z?"  # ISO timestamp
    r"|\b\d+\b"  # bare integers (PIDs, ports, counts)
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"  # UUIDs
)


def _normalise(line: str) -> str:
    """Return a normalised version of *line* suitable for equality comparison."""
    return _NOISE.sub("<X>", line).strip()


@dataclass
class DiffResult:
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    # --- convenience properties ---

    @property
    def total_a(self) -> int:
        return len(self.only_in_a) + len(self.common)

    @property
    def total_b(self) -> int:
        return len(self.only_in_b) + len(self.common)

    @property
    def common_count(self) -> int:
        return len(self.common)


def diff_logs(
    lines_a: Sequence[str],
    lines_b: Sequence[str],
    *,
    normalise: bool = True,
) -> DiffResult:
    """Compare two sequences of log lines.

    Parameters
    ----------
    lines_a, lines_b:
        Iterables of raw log lines (newlines are stripped automatically).
    normalise:
        When *True* (default) timestamps, integers and UUIDs are masked before
        comparison so that structurally identical lines still match.

    Returns
    -------
    DiffResult
        Three buckets: lines only in *a*, lines only in *b*, and common lines.
    """
    _key = _normalise if normalise else str.strip

    set_a = {_key(l) for l in lines_a if l.strip()}
    set_b = {_key(l) for l in lines_b if l.strip()}

    common_keys = set_a & set_b

    result = DiffResult()
    for line in lines_a:
        if line.strip() and _key(line) in common_keys:
            result.common.append(line.rstrip())
        elif line.strip():
            result.only_in_a.append(line.rstrip())

    for line in lines_b:
        if line.strip() and _key(line) not in common_keys:
            result.only_in_b.append(line.rstrip())

    return result


def format_diff(result: DiffResult, *, color: bool = True) -> str:
    """Render a human-readable diff summary."""
    RED = "\033[31m" if color else ""
    GREEN = "\033[32m" if color else ""
    RESET = "\033[0m" if color else ""

    lines: List[str] = []
    for l in result.only_in_a:
        lines.append(f"{RED}- {l}{RESET}")
    for l in result.only_in_b:
        lines.append(f"{GREEN}+ {l}{RESET}")
    lines.append(
        f"\n--- {len(result.only_in_a)} only in A | "
        f"{len(result.only_in_b)} only in B | "
        f"{result.common_count} common ---"
    )
    return "\n".join(lines)
