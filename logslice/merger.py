"""Merge multiple log files into a single chronologically sorted stream."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from logslice.parser import extract_timestamp


@dataclass
class MergeResult:
    lines: List[str] = field(default_factory=list)
    source_counts: dict = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.lines)


def _iter_tagged(path: Path) -> Iterator[tuple]:
    """Yield (timestamp_or_None, line, source_name) for every line in *path*."""
    source = path.name
    try:
        with path.open("r", errors="replace") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                ts = extract_timestamp(line)
                yield (ts, line, source)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Log file not found: {path}") from exc


def merge_logs(
    paths: Iterable[str | Path],
    *,
    stable: bool = True,
) -> MergeResult:
    """Merge log files, sorting lines by parsed timestamp where available.

    Lines without a detectable timestamp retain their original order relative
    to the file they came from and are placed *before* any timestamped line
    at the same heap position (i.e. they bubble to the top).

    Args:
        paths:  Iterable of file paths to merge.
        stable: When True (default) lines without timestamps keep file order.

    Returns:
        MergeResult with merged lines and per-source line counts.
    """
    resolved = [Path(p) for p in paths]
    result = MergeResult()

    # heap entries: (sort_key, file_index, line_index, line, source)
    # sort_key is (0, ts_str) for timestamped lines, (0, "") for others so
    # that non-timestamped lines sort before everything else.
    heap: list = []
    iterators = []

    for file_idx, path in enumerate(resolved):
        it = enumerate(_iter_tagged(path))
        iterators.append(it)
        result.source_counts[path.name] = 0

    def _push(file_idx: int, line_idx: int, ts: Optional[str], line: str, source: str) -> None:
        sort_key = ts if ts is not None else ""
        heapq.heappush(heap, (sort_key, file_idx, line_idx, line, source))

    # Seed the heap with the first line from each file.
    for file_idx, it in enumerate(iterators):
        try:
            line_idx, (ts, line, source) = next(it)
            _push(file_idx, line_idx, ts, line, source)
        except StopIteration:
            pass

    while heap:
        sort_key, file_idx, line_idx, line, source = heapq.heappop(heap)
        result.lines.append(line)
        result.source_counts[source] = result.source_counts.get(source, 0) + 1

        # Advance the exhausted iterator.
        try:
            next_line_idx, (ts, next_line, next_source) = next(iterators[file_idx])
            _push(file_idx, next_line_idx, ts, next_line, next_source)
        except StopIteration:
            pass

    return result
