"""Line-level annotation: attach tags or notes to specific log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Annotation:
    line_number: int
    original: str
    tag: str
    note: Optional[str] = None

    def __str__(self) -> str:
        note_part = f" — {self.note}" if self.note else ""
        return f"[{self.tag}] (L{self.line_number}){note_part}: {self.original.rstrip()}"


@dataclass
class AnnotateResult:
    annotations: List[Annotation] = field(default_factory=list)
    total_lines: int = 0

    @property
    def annotated_count(self) -> int:
        return len(self.annotations)


def _make_rule(pattern: str, tag: str, note: Optional[str]) -> Tuple[re.Pattern, str, Optional[str]]:
    return re.compile(pattern), tag, note


def annotate_lines(
    lines: List[str],
    rules: List[Tuple[str, str, Optional[str]]],
) -> AnnotateResult:
    """Apply (pattern, tag, note) rules to lines; collect matching annotations."""
    compiled = [_make_rule(pat, tag, note) for pat, tag, note in rules]
    result = AnnotateResult(total_lines=len(lines))
    for lineno, line in enumerate(lines, start=1):
        for regex, tag, note in compiled:
            if regex.search(line):
                result.annotations.append(
                    Annotation(line_number=lineno, original=line, tag=tag, note=note)
                )
                break  # first matching rule wins
    return result


def format_annotations(result: AnnotateResult, *, show_summary: bool = True) -> str:
    """Render annotations as human-readable text."""
    lines = [str(ann) for ann in result.annotations]
    if show_summary:
        lines.append(
            f"\n--- {result.annotated_count} annotation(s) across {result.total_lines} line(s) ---"
        )
    return "\n".join(lines)
