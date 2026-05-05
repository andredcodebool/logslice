"""Tests for logslice.exporter."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from logslice.exporter import export_csv, export_jsonl, export_result, export_txt
from logslice.formatter import SliceResult


@pytest.fixture()
def sample_result() -> SliceResult:
    return SliceResult(
        matched_lines=["2024-01-01 ERROR something broke", "2024-01-01 INFO all good"],
        total_lines=10,
        source_path="app.log",
    )


def test_export_txt_creates_file(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.txt"
    export_txt(sample_result, dest)
    assert dest.exists()
    lines = dest.read_text(encoding="utf-8").splitlines()
    assert lines == sample_result.matched_lines


def test_export_jsonl_valid_json(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.jsonl"
    export_jsonl(sample_result, dest)
    rows = [json.loads(l) for l in dest.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len(sample_result.matched_lines)
    assert rows[0]["line"] == sample_result.matched_lines[0]


def test_export_csv_has_header(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.csv"
    export_csv(sample_result, dest)
    with dest.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    assert rows[0] == ["line"]
    assert len(rows) == len(sample_result.matched_lines) + 1


def test_export_result_dispatches_txt(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.txt"
    export_result(sample_result, dest, fmt="txt")
    assert dest.exists()


def test_export_result_dispatches_jsonl(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.jsonl"
    export_result(sample_result, dest, fmt="jsonl")
    assert dest.exists()


def test_export_result_dispatches_csv(tmp_path: Path, sample_result: SliceResult) -> None:
    dest = tmp_path / "out.csv"
    export_result(sample_result, dest, fmt="csv")
    assert dest.exists()


def test_export_result_unknown_format_raises(tmp_path: Path, sample_result: SliceResult) -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_result(sample_result, tmp_path / "out.xml", fmt="xml")


def test_export_txt_empty_result(tmp_path: Path) -> None:
    result = SliceResult(matched_lines=[], total_lines=5, source_path="empty.log")
    dest = tmp_path / "empty.txt"
    export_txt(result, dest)
    assert dest.read_text(encoding="utf-8") == "\n"
