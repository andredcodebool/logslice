"""Tag log lines with user-defined labels based on regex rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TaggedLine:
    lineno: int
    text: str
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ",".join(self.tags)
        prefix = f"[{tag_str}] " if self.tags else ""
        return f"{prefix}{self.text}"


@dataclass
class TagResult:
    lines: List[TaggedLine]
    rules: List[Tuple[str, str]]  # (tag, pattern)

    @property
    def total(self) -> int:
        return len(self.lines)

    @property
    def tagged_count(self) -> int:
        return sum(1 for ln in self.lines if ln.tags)

    @property
    def tag_summary(self) -> dict:
        summary: dict = {}
        for ln in self.lines:
            for tag in ln.tags:
                summary[tag] = summary.get(tag, 0) + 1
        return summary


def build_tag_rules(raw_rules: List[str]) -> List[Tuple[str, re.Pattern]]:
    """Parse rules of the form 'LABEL=PATTERN' into (label, compiled_pattern)."""
    compiled = []
    for rule in raw_rules:
        if "=" not in rule:
            raise ValueError(f"Tag rule must be 'LABEL=PATTERN', got: {rule!r}")
        label, _, pattern = rule.partition("=")
        label = label.strip()
        pattern = pattern.strip()
        if not label:
            raise ValueError(f"Empty label in rule: {rule!r}")
        compiled.append((label, re.compile(pattern, re.IGNORECASE)))
    return compiled


def tag_lines(
    lines: List[str],
    raw_rules: List[str],
) -> TagResult:
    """Apply tag rules to each line and return a TagResult."""
    rules = build_tag_rules(raw_rules)
    tagged: List[TaggedLine] = []
    for i, text in enumerate(lines, start=1):
        matched_tags = [
            label for label, pat in rules if pat.search(text)
        ]
        tagged.append(TaggedLine(lineno=i, text=text, tags=matched_tags))
    return TagResult(
        lines=tagged,
        rules=[(label, pat.pattern) for label, pat in rules],
    )
