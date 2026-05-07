"""Redact sensitive patterns (emails, IPs, tokens, custom regex) from log lines."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Built-in sensitive patterns
_BUILTIN_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'),
    "ipv4": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "bearer": re.compile(r'(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*'),
    "uuid": re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
    "credit_card": re.compile(r'\b(?:\d[ -]?){13,16}\b'),
}

PLACEHOLDER = "[REDACTED]"


@dataclass
class RedactResult:
    lines: List[str]
    total: int
    redacted_count: int  # lines that had at least one substitution
    substitutions: int   # total number of replacements made


def _redacted_lines(result: RedactResult) -> List[str]:
    return result.lines


def build_patterns(
    builtins: Optional[List[str]] = None,
    custom: Optional[List[str]] = None,
) -> List[re.Pattern]:
    """Return compiled patterns from selected builtins + custom regex strings."""
    patterns: List[re.Pattern] = []
    for name in (builtins or []):
        if name in _BUILTIN_PATTERNS:
            patterns.append(_BUILTIN_PATTERNS[name])
        else:
            raise ValueError(f"Unknown builtin redaction pattern: {name!r}")
    for expr in (custom or []):
        patterns.append(re.compile(expr))
    return patterns


def redact_line(line: str, patterns: List[re.Pattern], placeholder: str = PLACEHOLDER):
    """Apply all patterns to a single line; return (new_line, count_of_subs)."""
    total_subs = 0
    for pat in patterns:
        line, n = pat.subn(placeholder, line)
        total_subs += n
    return line, total_subs


def redact_lines(
    lines: List[str],
    builtins: Optional[List[str]] = None,
    custom: Optional[List[str]] = None,
    placeholder: str = PLACEHOLDER,
) -> RedactResult:
    """Redact sensitive data from a list of log lines."""
    patterns = build_patterns(builtins, custom)
    out_lines: List[str] = []
    redacted_count = 0
    substitutions = 0
    for line in lines:
        new_line, subs = redact_line(line, patterns, placeholder)
        out_lines.append(new_line)
        substitutions += subs
        if subs > 0:
            redacted_count += 1
    return RedactResult(
        lines=out_lines,
        total=len(lines),
        redacted_count=redacted_count,
        substitutions=substitutions,
    )
