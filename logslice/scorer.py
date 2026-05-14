"""Score log lines by relevance using keyword weights and level severity."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

_LEVEL_SCORES: Dict[str, float] = {
    "fatal": 1.0,
    "critical": 1.0,
    "error": 0.8,
    "warn": 0.5,
    "warning": 0.5,
    "info": 0.2,
    "debug": 0.1,
    "trace": 0.05,
}

_LEVEL_RE = re.compile(
    r"\b(fatal|critical|error|warn(?:ing)?|info|debug|trace)\b", re.IGNORECASE
)


@dataclass
class ScoredLine:
    line: str
    score: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    lines: List[ScoredLine]
    threshold: float

    @property
    def total(self) -> int:
        return len(self.lines)

    @property
    def above_threshold(self) -> List[ScoredLine]:
        return [sl for sl in self.lines if sl.score >= self.threshold]


def _level_score(line: str) -> Tuple[float, Optional[str]]:
    m = _LEVEL_RE.search(line)
    if m:
        lvl = m.group(1).lower()
        return _LEVEL_SCORES.get(lvl, 0.0), lvl
    return 0.0, None


def build_keyword_patterns(keywords: List[str]) -> List[re.Pattern]:
    """Compile a list of keyword strings into case-insensitive patterns."""
    return [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]


def score_line(
    line: str,
    keyword_patterns: List[re.Pattern],
    keyword_weight: float = 0.3,
) -> ScoredLine:
    """Compute a relevance score in [0, 1] for a single log line."""
    reasons: List[str] = []
    total_score = 0.0

    lvl_score, lvl_name = _level_score(line)
    if lvl_name:
        total_score += lvl_score
        reasons.append(f"level:{lvl_name}")

    for pat in keyword_patterns:
        if pat.search(line):
            total_score += keyword_weight
            reasons.append(f"keyword:{pat.pattern}")

    final = min(total_score, 1.0)
    return ScoredLine(line=line, score=round(final, 4), reasons=reasons)


def score_lines(
    lines: List[str],
    keywords: Optional[List[str]] = None,
    keyword_weight: float = 0.3,
    threshold: float = 0.0,
) -> ScoreResult:
    """Score all lines and return a ScoreResult."""
    patterns = build_keyword_patterns(keywords or [])
    scored = [score_line(ln, patterns, keyword_weight) for ln in lines]
    return ScoreResult(lines=scored, threshold=threshold)
