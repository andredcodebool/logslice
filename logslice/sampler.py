"""Log line sampler — keep every Nth line or a random fraction."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class SampleResult:
    lines: List[str] = field(default_factory=list)
    total_input: int = 0
    total_output: int = 0

    @property
    def ratio(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.total_output / self.total_input


def sample_every_n(lines: Iterable[str], n: int) -> SampleResult:
    """Keep every *n*-th line (1-based index). n must be >= 1."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    result = SampleResult()
    for idx, line in enumerate(lines, start=1):
        result.total_input += 1
        if idx % n == 0:
            result.lines.append(line)
            result.total_output += 1
    return result


def sample_random(
    lines: Iterable[str],
    fraction: float,
    seed: Optional[int] = None,
) -> SampleResult:
    """Keep each line with probability *fraction* in (0, 1]."""
    if not (0.0 < fraction <= 1.0):
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")

    rng = random.Random(seed)
    result = SampleResult()
    for line in lines:
        result.total_input += 1
        if rng.random() < fraction:
            result.lines.append(line)
            result.total_output += 1
    return result


def sample_head(lines: Iterable[str], count: int) -> SampleResult:
    """Keep only the first *count* lines."""
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")

    result = SampleResult()
    for line in lines:
        result.total_input += 1
        if result.total_output < count:
            result.lines.append(line)
            result.total_output += 1
    return result
