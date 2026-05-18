"""Trace a specific token (e.g. request-id, session-id) across log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TraceGroup:
    token: str
    lines: List[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.lines)


@dataclass
class TraceResult:
    groups: Dict[str, TraceGroup] = field(default_factory=dict)
    total_scanned: int = 0

    @property
    def total_matched(self) -> int:
        return sum(len(g) for g in self.groups.values())

    @property
    def token_count(self) -> int:
        return len(self.groups)


def _extract_tokens(line: str, pattern: re.Pattern) -> List[str]:
    """Return all unique tokens found in *line* by *pattern*."""
    return list(dict.fromkeys(pattern.findall(line)))


def trace_lines(
    lines: List[str],
    token_pattern: str,
    token_filter: Optional[str] = None,
) -> TraceResult:
    """Scan *lines* and group them by extracted token.

    Parameters
    ----------
    lines:
        Raw log lines to scan.
    token_pattern:
        Regex with at least one capturing group that identifies the token
        (e.g. ``r'request_id=(\S+)'``).
    token_filter:
        If given, only keep groups whose token matches this exact string.
    """
    compiled = re.compile(token_pattern)
    result = TraceResult()

    for line in lines:
        result.total_scanned += 1
        tokens = _extract_tokens(line, compiled)
        for token in tokens:
            if token_filter is not None and token != token_filter:
                continue
            if token not in result.groups:
                result.groups[token] = TraceGroup(token=token)
            result.groups[token].lines.append(line)

    return result


def format_trace(result: TraceResult, show_counts: bool = False) -> str:
    """Render a TraceResult as human-readable text."""
    parts: List[str] = []
    for token, group in result.groups.items():
        header = f"=== token: {token} ({len(group)} lines) ==="
        parts.append(header)
        parts.extend(group.lines)
    if show_counts:
        parts.append(
            f"\n[trace] tokens={result.token_count}  "
            f"matched={result.total_matched}  "
            f"scanned={result.total_scanned}"
        )
    return "\n".join(parts)
