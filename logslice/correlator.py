"""correlator.py – correlate log lines across multiple files by shared tokens.

A *correlation token* is a value extracted via a regex group named ``token``
(e.g. a request-id, trace-id, session-id).  Lines that share the same token
value are grouped together so you can trace a single request across several
log files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class CorrelatedGroup:
    """All lines that share a common token value."""
    token: str
    lines: List[Tuple[str, str]] = field(default_factory=list)  # (source, line)

    def __len__(self) -> int:
        return len(self.lines)


@dataclass
class CorrelateResult:
    """Outcome of a correlation run."""
    groups: Dict[str, CorrelatedGroup] = field(default_factory=dict)
    unmatched: List[Tuple[str, str]] = field(default_factory=list)  # (source, line)


def total(result: CorrelateResult) -> int:
    """Total lines processed (matched + unmatched)."""
    matched = sum(len(g) for g in result.groups.values())
    return matched + len(result.unmatched)


def group_count(result: CorrelateResult) -> int:
    """Number of distinct correlation groups."""
    return len(result.groups)


def correlate(
    sources: Iterable[Tuple[str, Iterable[str]]],
    pattern: str,
) -> CorrelateResult:
    """Correlate lines from *sources* using *pattern*.

    *sources* is an iterable of ``(label, lines)`` pairs.
    *pattern* must contain a named group ``(?P<token>...)``.

    Lines whose token matches an existing group are appended to that group;
    lines with no token match are added to *unmatched*.
    """
    compiled = re.compile(pattern)
    if "token" not in compiled.groupindex:
        raise ValueError("pattern must contain a named group 'token'")

    result = CorrelateResult()
    for label, lines in sources:
        for line in lines:
            line = line.rstrip("\n")
            m = compiled.search(line)
            if m:
                tok = m.group("token")
                if tok not in result.groups:
                    result.groups[tok] = CorrelatedGroup(token=tok)
                result.groups[tok].lines.append((label, line))
            else:
                result.unmatched.append((label, line))
    return result


def format_correlation(result: CorrelateResult, show_unmatched: bool = False) -> str:
    """Return a human-readable string for *result*."""
    parts: List[str] = []
    for tok, grp in sorted(result.groups.items()):
        parts.append(f"[token={tok}]  ({len(grp)} lines)")
        for src, ln in grp.lines:
            parts.append(f"  {src}: {ln}")
    if show_unmatched and result.unmatched:
        parts.append(f"[unmatched]  ({len(result.unmatched)} lines)")
        for src, ln in result.unmatched:
            parts.append(f"  {src}: {ln}")
    return "\n".join(parts)
