"""Tests for logslice.formatter."""

import json
from datetime import datetime

import pytest

from logslice.formatter import SliceResult, format_output, format_jsonl


@pytest.fixture()
def sample_result():
    return SliceResult(
        lines=["2024-01-01T10:00:00 INFO hello", "2024-01-01T10:01:00 ERROR world"],
        matched_count=2,
        total_count=5,
        start_time=datetime(2024, 1, 1, 10, 0, 0),
        end_time=datetime(2024, 1, 1, 10, 1, 0),
    )


def test_match_ratio_zero_total():
    result = SliceResult()
    assert result.match_ratio == 0.0


def test_match_ratio_calculated(sample_result):
    assert sample_result.match_ratio == pytest.approx(0.4)


def test_format_output_contains_lines(sample_result):
    output = format_output(sample_result)
    assert "INFO hello" in output
    assert "ERROR world" in output


def test_format_output_summary_present(sample_result):
    output = format_output(sample_result, show_summary=True)
    assert "logslice summary" in output
    assert "Matched lines : 2" in output
    assert "Total lines   : 5" in output
    assert "40.0%" in output


def test_format_output_no_summary(sample_result):
    output = format_output(sample_result, show_summary=False)
    assert "logslice summary" not in output


def test_format_output_timestamps(sample_result):
    output = format_output(sample_result)
    assert "2024-01-01T10:00:00" in output
    assert "2024-01-01T10:01:00" in output


def test_format_output_no_timestamps_when_none():
    result = SliceResult(lines=["line1"], matched_count=1, total_count=1)
    output = format_output(result)
    assert "First match" not in output
    assert "Last match" not in output


def test_format_jsonl_valid_json(sample_result):
    output = format_jsonl(sample_result)
    rows = output.strip().splitlines()
    assert len(rows) == 2
    for row in rows:
        obj = json.loads(row)
        assert "line" in obj


def test_format_jsonl_content(sample_result):
    output = format_jsonl(sample_result)
    assert "INFO hello" in output
    assert "ERROR world" in output


def test_format_jsonl_empty():
    result = SliceResult()
    assert format_jsonl(result) == ""
