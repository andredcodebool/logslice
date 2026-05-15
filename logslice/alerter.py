"""Alert rule matching: flag lines that exceed thresholds or match patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class AlertRule:
    label: str
    pattern: re.Pattern
    level: Optional[str] = None  # e.g. "ERROR", "FATAL"


@dataclass
class AlertHit:
    line_no: int
    line: str
    rule_label: str

    def __str__(self) -> str:
        return f"[{self.rule_label}] line {self.line_no}: {self.line.rstrip()}"


@dataclass
class AlertResult:
    lines: List[str]
    hits: List[AlertHit]
    rules: List[AlertRule]

    @property
    def total(self) -> int:
        return len(self.lines)

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    @property
    def hit_rate(self) -> float:
        return self.hit_count / self.total if self.total else 0.0


def build_rules(specs: List[str]) -> List[AlertRule]:
    """Parse rule specs of the form 'LABEL=PATTERN' or 'LABEL=PATTERN:LEVEL'."""
    rules: List[AlertRule] = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Alert rule missing '=': {spec!r}")
        label, rest = spec.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError(f"Alert rule label is empty in: {spec!r}")
        level: Optional[str] = None
        if ":" in rest:
            pattern_str, level = rest.rsplit(":", 1)
            level = level.strip().upper() or None
        else:
            pattern_str = rest
        rules.append(AlertRule(label=label, pattern=re.compile(pattern_str.strip()), level=level))
    return rules


def _line_level(line: str) -> Optional[str]:
    for lvl in ("FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"):
        if lvl in line.upper():
            return lvl
    return None


def check_alerts(lines: List[str], rules: List[AlertRule]) -> AlertResult:
    """Scan lines against all alert rules, returning every hit."""
    hits: List[AlertHit] = []
    for i, line in enumerate(lines, start=1):
        for rule in rules:
            if rule.pattern.search(line):
                if rule.level is None or rule.level in (_line_level(line) or ""):
                    hits.append(AlertHit(line_no=i, line=line, rule_label=rule.label))
                    break
    return AlertResult(lines=lines, hits=hits, rules=rules)
