"""Tests for logslice.dedup and logslice.cli_dedup."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.dedup import DedupResult, _normalise, deduplicate, top_repeated
from logslice.cli_dedup import add_dedup_subparser, run_dedup


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------

def test_normalise_strips_timestamp():
    line = "2024-01-15T12:00:00Z INFO server started"
    assert "<X>" in _normalise(line)
    assert "INFO server started" in _normalise(line)


def test_normalise_strips_integers():
    assert _normalise("retried 3 times") == _normalise("retried 7 times")


def test_normalise_strips_uuid():
    a = _normalise("user 123e4567-e89b-12d3-a456-426614174000 logged in")
    b = _normalise("user aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee logged in")
    assert a == b


# ---------------------------------------------------------------------------
# deduplicate — global mode
# ---------------------------------------------------------------------------

def test_dedup_global_removes_duplicates():
    lines = ["INFO start\n", "INFO start\n", "ERROR boom\n"]
    result = deduplicate(lines)
    assert result.total_unique == 2
    assert result.removed == 1


def test_dedup_global_preserves_order():
    lines = ["A\n", "B\n", "A\n", "C\n"]
    result = deduplicate(lines)
    assert result.unique_lines == ["A\n", "B\n", "C\n"]


def test_dedup_global_all_unique():
    lines = ["one\n", "two\n", "three\n"]
    result = deduplicate(lines)
    assert result.total_unique == 3
    assert result.removed == 0


def test_dedup_global_normalised_match():
    lines = [
        "2024-01-01 INFO request took 120ms\n",
        "2024-01-02 INFO request took 95ms\n",
    ]
    result = deduplicate(lines)
    assert result.total_unique == 1


# ---------------------------------------------------------------------------
# deduplicate — consecutive mode
# ---------------------------------------------------------------------------

def test_dedup_consecutive_keeps_non_adjacent():
    lines = ["A\n", "B\n", "A\n"]
    result = deduplicate(lines, consecutive_only=True)
    assert result.total_unique == 3  # A appears again after B


def test_dedup_consecutive_collapses_adjacent():
    lines = ["A\n", "A\n", "A\n", "B\n"]
    result = deduplicate(lines, consecutive_only=True)
    assert result.total_unique == 2


# ---------------------------------------------------------------------------
# top_repeated
# ---------------------------------------------------------------------------

def test_top_repeated_returns_correct_order():
    lines = ["X\n"] * 5 + ["Y\n"] * 3 + ["Z\n"]
    result = deduplicate(lines)
    top = top_repeated(result, 2)
    assert top[0][1] == 5
    assert top[1][1] == 3


def test_top_repeated_empty():
    result = DedupResult()
    assert top_repeated(result, 5) == []


# ---------------------------------------------------------------------------
# CLI — run_dedup
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(
        "2024-01-01 INFO hello\n"
        "2024-01-02 INFO hello\n"
        "2024-01-03 ERROR crash\n",
        encoding="utf-8",
    )
    return p


def _make_args(file: str, **kwargs) -> argparse.Namespace:
    defaults = dict(file=file, consecutive=False, output=None, stats=False, top=0)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_dedup_missing_file(tmp_path: Path):
    args = _make_args(str(tmp_path / "missing.log"))
    assert run_dedup(args) == 1


def test_run_dedup_writes_output(log_file: Path, tmp_path: Path):
    out = tmp_path / "out.log"
    args = _make_args(str(log_file), output=str(out))
    rc = run_dedup(args)
    assert rc == 0
    content = out.read_text()
    assert "ERROR crash" in content
    # Two INFO hello lines should be collapsed to one
    assert content.count("INFO hello") == 1


def test_add_dedup_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_dedup_subparser(sub)
    ns = parser.parse_args(["dedup", "myfile.log"])
    assert ns.file == "myfile.log"
    assert ns.consecutive is False
