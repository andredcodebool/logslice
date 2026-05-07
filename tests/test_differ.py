"""Tests for logslice.differ."""

from __future__ import annotations

import pytest

from logslice.differ import DiffResult, _normalise, diff_logs, format_diff


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------

def test_normalise_strips_timestamp():
    line = "2024-01-15T12:34:56.789Z INFO server started"
    result = _normalise(line)
    assert "2024" not in result
    assert "INFO server started" in result


def test_normalise_strips_integers():
    result = _normalise("pid=1234 connected")
    assert "1234" not in result
    assert "connected" in result


def test_normalise_strips_uuid():
    uuid = "550e8400-e29b-41d4-a716-446655440000"
    result = _normalise(f"request {uuid} received")
    assert uuid not in result
    assert "received" in result


# ---------------------------------------------------------------------------
# diff_logs — basic behaviour
# ---------------------------------------------------------------------------

LINES_A = [
    "2024-01-01 INFO  app started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 DEBUG heartbeat 1\n",
]

LINES_B = [
    "2024-01-02 INFO  app started\n",   # same structure → common
    "2024-01-02 WARN  memory low\n",    # only in B
    "2024-01-02 DEBUG heartbeat 2\n",   # same structure → common
]


def test_diff_common_lines_detected():
    result = diff_logs(LINES_A, LINES_B)
    assert result.common_count == 2


def test_diff_only_in_a():
    result = diff_logs(LINES_A, LINES_B)
    assert len(result.only_in_a) == 1
    assert "disk full" in result.only_in_a[0]


def test_diff_only_in_b():
    result = diff_logs(LINES_A, LINES_B)
    assert len(result.only_in_b) == 1
    assert "memory low" in result.only_in_b[0]


def test_diff_total_counts():
    result = diff_logs(LINES_A, LINES_B)
    assert result.total_a == len([l for l in LINES_A if l.strip()])
    assert result.total_b == len([l for l in LINES_B if l.strip()])


def test_diff_empty_inputs():
    result = diff_logs([], [])
    assert result.only_in_a == []
    assert result.only_in_b == []
    assert result.common == []


def test_diff_identical_inputs():
    lines = ["INFO started\n", "DEBUG ping\n"]
    result = diff_logs(lines, lines)
    assert result.only_in_a == []
    assert result.only_in_b == []
    assert result.common_count == 2


def test_diff_no_normalise():
    """Without normalisation, lines differing only in timestamp are NOT common."""
    result = diff_logs(LINES_A, LINES_B, normalise=False)
    # All lines differ because dates differ
    assert result.common_count == 0


def test_diff_blank_lines_ignored():
    result = diff_logs(["\n", "  \n"], ["\n"])
    assert result.common_count == 0
    assert result.only_in_a == []
    assert result.only_in_b == []


# ---------------------------------------------------------------------------
# format_diff
# ---------------------------------------------------------------------------

def test_format_diff_contains_summary():
    result = diff_logs(LINES_A, LINES_B)
    output = format_diff(result, color=False)
    assert "only in A" in output
    assert "only in B" in output
    assert "common" in output


def test_format_diff_prefixes():
    result = diff_logs(LINES_A, LINES_B)
    output = format_diff(result, color=False)
    assert "- " in output   # line only in A
    assert "+ " in output   # line only in B


def test_format_diff_color_codes():
    result = diff_logs(LINES_A, LINES_B)
    colored = format_diff(result, color=True)
    assert "\033[" in colored


def test_format_diff_no_color():
    result = diff_logs(LINES_A, LINES_B)
    plain = format_diff(result, color=False)
    assert "\033[" not in plain
