"""Tests for logslice.splitter and logslice.cli_splitter."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from logslice.splitter import (
    SplitResult,
    split_by_lines,
    split_by_size,
    split_by_time,
    write_chunks,
)
from logslice.cli_splitter import add_splitter_subparser, run_splitter


LINES = [f"2024-01-01 00:{m:02d}:00 INFO message {i}\n" for i, m in enumerate(range(20))]


# --- split_by_lines ---

def test_split_by_lines_basic():
    result = split_by_lines(LINES, 5)
    assert result.chunk_count == 4
    assert result.source_lines == 20
    assert result.mode == "lines"


def test_split_by_lines_all_in_one_chunk():
    result = split_by_lines(LINES, 100)
    assert result.chunk_count == 1
    assert result.chunks[0] == LINES


def test_split_by_lines_invalid_raises():
    with pytest.raises(ValueError):
        split_by_lines(LINES, 0)


def test_split_by_lines_preserves_content():
    result = split_by_lines(LINES, 7)
    flat = [l for chunk in result.chunks for l in chunk]
    assert flat == LINES


# --- split_by_size ---

def test_split_by_size_creates_multiple_chunks():
    result = split_by_size(LINES, 100)
    assert result.chunk_count > 1
    assert result.mode == "size"


def test_split_by_size_large_limit_one_chunk():
    result = split_by_size(LINES, 1_000_000)
    assert result.chunk_count == 1


def test_split_by_size_invalid_raises():
    with pytest.raises(ValueError):
        split_by_size(LINES, 0)


def test_split_by_size_preserves_content():
    result = split_by_size(LINES, 80)
    flat = [l for chunk in result.chunks for l in chunk]
    assert flat == LINES


# --- split_by_time ---

def test_split_by_time_creates_chunks():
    result = split_by_time(LINES, 5)
    assert result.chunk_count >= 1
    assert result.mode == "time"


def test_split_by_time_single_chunk_for_large_interval():
    result = split_by_time(LINES, 999)
    assert result.chunk_count == 1


def test_split_by_time_invalid_raises():
    with pytest.raises(ValueError):
        split_by_time(LINES, 0)


def test_split_by_time_preserves_content():
    result = split_by_time(LINES, 5)
    flat = [l for chunk in result.chunks for l in chunk]
    assert flat == LINES


# --- write_chunks ---

def test_write_chunks_creates_files(tmp_path):
    result = split_by_lines(LINES, 5)
    paths = write_chunks(result, str(tmp_path), stem="part")
    assert len(paths) == result.chunk_count
    for p in paths:
        assert Path(p).exists()


def test_write_chunks_content_correct(tmp_path):
    result = split_by_lines(LINES, 5)
    paths = write_chunks(result, str(tmp_path))
    all_lines = []
    for p in sorted(paths):
        all_lines.extend(Path(p).read_text().splitlines(keepends=True))
    assert all_lines == LINES


# --- CLI ---

def test_add_splitter_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_splitter_subparser(sub)
    args = parser.parse_args(["split", "myfile.log", "--mode", "lines"])
    assert args.mode == "lines"


def test_run_splitter_lines(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("".join(LINES))
    out = tmp_path / "out"
    args = argparse.Namespace(
        file=str(log),
        mode="lines",
        chunk_lines=5,
        chunk_bytes=1_048_576,
        interval=60,
        output_dir=str(out),
        stem="chunk",
    )
    run_splitter(args)  # should not raise
    assert len(list(out.glob("*.log"))) == 4


def test_run_splitter_missing_file_exits(tmp_path, capsys):
    args = argparse.Namespace(
        file=str(tmp_path / "missing.log"),
        mode="lines",
        chunk_lines=5,
        chunk_bytes=1_048_576,
        interval=60,
        output_dir=str(tmp_path / "out"),
        stem="chunk",
    )
    with pytest.raises(SystemExit):
        run_splitter(args)
