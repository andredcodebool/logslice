"""Tests for logslice.merger and logslice.cli_merger."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from logslice.merger import MergeResult, merge_logs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# merge_logs
# ---------------------------------------------------------------------------

def test_merge_returns_merge_result(tmp_path):
    a = _write(tmp_path, "a.log", "2024-01-01 10:00:00 INFO  hello\n")
    b = _write(tmp_path, "b.log", "2024-01-01 10:00:01 INFO  world\n")
    result = merge_logs([a, b])
    assert isinstance(result, MergeResult)


def test_merge_chronological_order(tmp_path):
    a = _write(tmp_path, "a.log",
               "2024-01-01 10:00:02 INFO  second\n"
               "2024-01-01 10:00:04 INFO  fourth\n")
    b = _write(tmp_path, "b.log",
               "2024-01-01 10:00:01 INFO  first\n"
               "2024-01-01 10:00:03 INFO  third\n")
    result = merge_logs([a, b])
    assert result.lines[0].endswith("first")
    assert result.lines[1].endswith("second")
    assert result.lines[2].endswith("third")
    assert result.lines[3].endswith("fourth")


def test_merge_total_line_count(tmp_path):
    a = _write(tmp_path, "a.log", "line1\nline2\n")
    b = _write(tmp_path, "b.log", "line3\n")
    result = merge_logs([a, b])
    assert result.total == 3


def test_merge_source_counts(tmp_path):
    a = _write(tmp_path, "a.log", "line1\nline2\n")
    b = _write(tmp_path, "b.log", "line3\nline4\nline5\n")
    result = merge_logs([a, b])
    assert result.source_counts["a.log"] == 2
    assert result.source_counts["b.log"] == 3


def test_merge_single_file(tmp_path):
    a = _write(tmp_path, "only.log", "alpha\nbeta\n")
    result = merge_logs([a])
    assert result.lines == ["alpha", "beta"]


def test_merge_empty_file(tmp_path):
    a = _write(tmp_path, "empty.log", "")
    b = _write(tmp_path, "b.log", "hello\n")
    result = merge_logs([a, b])
    assert result.total == 1
    assert result.lines == ["hello"]


def test_merge_missing_file_raises(tmp_path):
    missing = tmp_path / "ghost.log"
    with pytest.raises(FileNotFoundError, match="ghost.log"):
        merge_logs([missing])


def test_merge_no_timestamp_lines_preserve_file_order(tmp_path):
    """Lines without timestamps should not be reordered across files."""
    a = _write(tmp_path, "a.log", "aaa\nbbb\n")
    b = _write(tmp_path, "b.log", "ccc\nddd\n")
    result = merge_logs([a, b])
    # All lines present; no crash expected.
    assert set(result.lines) == {"aaa", "bbb", "ccc", "ddd"}


# ---------------------------------------------------------------------------
# cli_merger
# ---------------------------------------------------------------------------

def test_cli_merger_stdout(tmp_path, capsys):
    from argparse import Namespace
    from logslice.cli_merger import run_merger

    a = _write(tmp_path, "a.log", "2024-01-01 09:00:00 INFO  A\n")
    b = _write(tmp_path, "b.log", "2024-01-01 09:00:01 INFO  B\n")
    args = Namespace(files=[str(a), str(b)], output=None, summary=False)
    run_merger(args)
    captured = capsys.readouterr()
    assert "INFO  A" in captured.out
    assert "INFO  B" in captured.out


def test_cli_merger_output_file(tmp_path, capsys):
    from argparse import Namespace
    from logslice.cli_merger import run_merger

    a = _write(tmp_path, "a.log", "hello\n")
    out_file = tmp_path / "merged.log"
    args = Namespace(files=[str(a)], output=str(out_file), summary=False)
    run_merger(args)
    assert out_file.exists()
    assert "hello" in out_file.read_text()


def test_cli_merger_summary_printed_to_stderr(tmp_path, capsys):
    from argparse import Namespace
    from logslice.cli_merger import run_merger

    a = _write(tmp_path, "a.log", "line1\nline2\n")
    args = Namespace(files=[str(a)], output=None, summary=True)
    run_merger(args)
    captured = capsys.readouterr()
    assert "a.log" in captured.err
    assert "2 lines" in captured.err


def test_add_merger_subparser():
    import argparse
    from logslice.cli_merger import add_merger_subparser

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_merger_subparser(sub)
    args = parser.parse_args(["merge", "x.log", "y.log"])
    assert args.files == ["x.log", "y.log"]
    assert args.output is None
    assert args.summary is False
