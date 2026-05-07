"""Line and block truncation utilities for logslice output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TruncateResult:
    lines: List[str]
    original_count: int
    truncated_count: int
    limit: int
    mode: str  # 'head', 'tail', 'middle'


def _removed(result: TruncateResult) -> int:
    return result.original_count - result.truncated_count


def truncate_head(lines: List[str], limit: int) -> TruncateResult:
    """Keep only the first *limit* lines."""
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    kept = lines[:limit]
    return TruncateResult(
        lines=kept,
        original_count=len(lines),
        truncated_count=len(kept),
        limit=limit,
        mode="head",
    )


def truncate_tail(lines: List[str], limit: int) -> TruncateResult:
    """Keep only the last *limit* lines."""
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    kept = lines[-limit:] if len(lines) > limit else lines[:]
    return TruncateResult(
        lines=kept,
        original_count=len(lines),
        truncated_count=len(kept),
        limit=limit,
        mode="tail",
    )


def truncate_middle(lines: List[str], limit: int) -> TruncateResult:
    """Keep first half and last half of *limit* lines, dropping the middle."""
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    if len(lines) <= limit:
        return TruncateResult(
            lines=lines[:],
            original_count=len(lines),
            truncated_count=len(lines),
            limit=limit,
            mode="middle",
        )
    half = limit // 2
    head = lines[:half]
    tail = lines[-(limit - half):]
    placeholder = f"... [{len(lines) - limit} lines omitted] ..."
    kept = head + [placeholder] + tail
    return TruncateResult(
        lines=kept,
        original_count=len(lines),
        truncated_count=limit,
        limit=limit,
        mode="middle",
    )


def truncate_lines(
    lines: List[str],
    limit: int,
    mode: str = "head",
) -> TruncateResult:
    """Dispatch to the appropriate truncation strategy."""
    dispatch = {"head": truncate_head, "tail": truncate_tail, "middle": truncate_middle}
    if mode not in dispatch:
        raise ValueError(f"Unknown mode {mode!r}; choose from {list(dispatch)}.")
    return dispatch[mode](lines, limit)
