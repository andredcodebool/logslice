"""Log line normalizer: strips or replaces noisy fields for cleaner diffing/dedup."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Built-in substitution patterns: (name, pattern, replacement)
_BUILTIN: dict[str, tuple[str, str]] = {
    "timestamp": (r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?", "<TS>"),
    "ipv4": (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IP>"),
    "uuid": (r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<UUID>"),
    "integer": (r"\b\d+\b", "<N>"),
    "email": (r"[\w.+-]+@[\w-]+\.[\w.]+", "<EMAIL>"),
    "url": (r"https?://[^\s]+", "<URL>"),
}


@dataclass
class NormalizeResult:
    original_lines: List[str]
    normalized_lines: List[str]
    rules_applied: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.original_lines)

    @property
    def changed_count(self) -> int:
        return sum(1 for o, n in zip(self.original_lines, self.normalized_lines) if o != n)


def build_rules(names: List[str], custom: Optional[List[str]] = None) -> List[tuple[re.Pattern, str]]:
    """Compile substitution rules from built-in names and optional custom regex=replacement pairs."""
    rules: List[tuple[re.Pattern, str]] = []
    for name in names:
        if name not in _BUILTIN:
            raise ValueError(f"Unknown built-in rule: '{name}'. Available: {list(_BUILTIN)}")
        pattern, replacement = _BUILTIN[name]
        rules.append((re.compile(pattern), replacement))
    for entry in custom or []:
        if "=" not in entry:
            raise ValueError(f"Custom rule must be 'pattern=replacement', got: {entry!r}")
        pat, _, repl = entry.partition("=")
        rules.append((re.compile(pat), repl))
    return rules


def normalize_line(line: str, rules: List[tuple[re.Pattern, str]]) -> str:
    """Apply all substitution rules to a single line."""
    for pattern, replacement in rules:
        line = pattern.sub(replacement, line)
    return line


def normalize_lines(
    lines: List[str],
    builtin_rules: Optional[List[str]] = None,
    custom_rules: Optional[List[str]] = None,
) -> NormalizeResult:
    """Normalize a list of log lines by applying substitution rules."""
    builtin_rules = builtin_rules or []
    rules = build_rules(builtin_rules, custom_rules)
    normalized = [normalize_line(line, rules) for line in lines]
    return NormalizeResult(
        original_lines=lines,
        normalized_lines=normalized,
        rules_applied=builtin_rules + [r.split("=")[0] for r in (custom_rules or [])],
    )
