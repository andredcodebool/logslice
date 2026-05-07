"""Split a log file into multiple chunks by line count, size, or time boundary."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from logslice.parser import extract_timestamp


@dataclass
class SplitResult:
    chunks: List[List[str]] = field(default_factory=list)
    mode: str = "lines"
    source_lines: int = 0

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


def split_by_lines(lines: List[str], chunk_size: int) -> SplitResult:
    """Split lines into chunks of at most *chunk_size* lines each."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    chunks = [lines[i : i + chunk_size] for i in range(0, len(lines), chunk_size)]
    return SplitResult(chunks=chunks, mode="lines", source_lines=len(lines))


def split_by_size(lines: List[str], max_bytes: int) -> SplitResult:
    """Split lines into chunks where each chunk is at most *max_bytes* bytes."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")
    chunks: List[List[str]] = []
    current: List[str] = []
    current_size = 0
    for line in lines:
        line_size = len(line.encode())
        if current and current_size + line_size > max_bytes:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(line)
        current_size += line_size
    if current:
        chunks.append(current)
    return SplitResult(chunks=chunks, mode="size", source_lines=len(lines))


def split_by_time(lines: List[str], interval_minutes: int) -> SplitResult:
    """Split lines into chunks separated by *interval_minutes* time boundaries."""
    if interval_minutes < 1:
        raise ValueError("interval_minutes must be >= 1")
    from datetime import timedelta

    chunks: List[List[str]] = []
    current: List[str] = []
    boundary = None
    for line in lines:
        ts = extract_timestamp(line)
        if ts is not None:
            if boundary is None:
                boundary = ts + timedelta(minutes=interval_minutes)
            elif ts >= boundary:
                if current:
                    chunks.append(current)
                    current = []
                boundary = ts + timedelta(minutes=interval_minutes)
        current.append(line)
    if current:
        chunks.append(current)
    return SplitResult(chunks=chunks, mode="time", source_lines=len(lines))


def write_chunks(result: SplitResult, output_dir: str, stem: str = "chunk") -> List[str]:
    """Write each chunk to *output_dir* as ``<stem>_NNN.log``. Returns file paths."""
    os.makedirs(output_dir, exist_ok=True)
    paths: List[str] = []
    for idx, chunk in enumerate(result.chunks):
        path = str(Path(output_dir) / f"{stem}_{idx:03d}.log")
        with open(path, "w") as fh:
            fh.writelines(chunk)
        paths.append(path)
    return paths
