"""pipeline.py — Chain multiple logslice operations into a single pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional

LineTransform = Callable[[str], Optional[str]]


@dataclass
class PipelineResult:
    """Holds the output of a pipeline run."""
    lines_in: int
    lines_out: int
    dropped: int
    output: List[str]
    stage_names: List[str] = field(default_factory=list)

    @property
    def retention_rate(self) -> float:
        if self.lines_in == 0:
            return 0.0
        return self.lines_out / self.lines_in


@dataclass
class Stage:
    """A named transformation stage."""
    name: str
    transform: LineTransform

    def apply(self, line: str) -> Optional[str]:
        return self.transform(line)


def build_pipeline(stages: List[Stage]) -> "Pipeline":
    """Convenience constructor."""
    return Pipeline(stages=stages)


class Pipeline:
    """Ordered sequence of Stage objects applied line-by-line."""

    def __init__(self, stages: Optional[List[Stage]] = None) -> None:
        self.stages: List[Stage] = stages or []

    def add_stage(self, stage: Stage) -> "Pipeline":
        self.stages.append(stage)
        return self

    def run(self, lines: Iterable[str]) -> PipelineResult:
        input_lines = list(lines)
        current: List[str] = input_lines

        for stage in self.stages:
            next_lines: List[str] = []
            for line in current:
                result = stage.apply(line)
                if result is not None:
                    next_lines.append(result)
            current = next_lines

        return PipelineResult(
            lines_in=len(input_lines),
            lines_out=len(current),
            dropped=len(input_lines) - len(current),
            output=current,
            stage_names=[s.name for s in self.stages],
        )
