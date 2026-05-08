"""Tests for logslice.profiler."""

from __future__ import annotations

import pytest

from logslice.profiler import (
    ProfileResult,
    _parse_ts,
    _window_key,
    profile_lines,
)
from datetime import datetime


# ---------------------------------------------------------------------------
# _parse_ts
# ---------------------------------------------------------------------------

def test_parse_ts_iso_space():
    dt = _parse_ts("2024-01-15 12:30:45 INFO starting")
    assert dt == datetime(2024, 1, 15, 12, 30, 45)


def test_parse_ts_iso_T():
    dt = _parse_ts("2024-01-15T08:00:00 DEBUG ok")
    assert dt == datetime(2024, 1, 15, 8, 0, 0)


def test_parse_ts_no_timestamp_returns_none():
    assert _parse_ts("no timestamp here") is None


def test_parse_ts_malformed_returns_none():
    assert _parse_ts("9999-99-99 99:99:99 bad") is None


# ---------------------------------------------------------------------------
# _window_key
# ---------------------------------------------------------------------------

def test_window_key_60s_boundary():
    dt = datetime(2024, 1, 15, 12, 30, 45)
    key = _window_key(dt, 60)
    # should truncate to :30:00
    assert key == "2024-01-15 12:30:00"


def test_window_key_3600s_boundary():
    dt = datetime(2024, 1, 15, 12, 45, 0)
    key = _window_key(dt, 3600)
    assert key.endswith("00:00")


# ---------------------------------------------------------------------------
# profile_lines
# ---------------------------------------------------------------------------

LINES = [
    "2024-01-15 10:00:00 INFO  line 1",
    "2024-01-15 10:00:10 INFO  line 2",
    "2024-01-15 10:00:20 WARN  line 3",
    "2024-01-15 10:01:05 ERROR line 4",
    "2024-01-15 10:01:15 INFO  line 5",
    "no timestamp here",
]


def test_profile_returns_profile_result():
    result = profile_lines(LINES)
    assert isinstance(result, ProfileResult)


def test_profile_total_lines():
    result = profile_lines(LINES)
    assert result.total_lines == 6


def test_profile_timestamped_lines():
    result = profile_lines(LINES)
    assert result.timestamped_lines == 5


def test_profile_duration():
    result = profile_lines(LINES)
    # 10:00:00 -> 10:01:15 = 75 seconds
    assert result.duration_seconds == pytest.approx(75.0)


def test_profile_lines_per_second():
    result = profile_lines(LINES)
    assert result.lines_per_second == pytest.approx(5 / 75, rel=1e-3)


def test_profile_busiest_window_not_empty():
    result = profile_lines(LINES, window_seconds=60)
    key, count = result.busiest_window
    assert count > 0
    assert key != ""


def test_profile_busiest_window_correct():
    result = profile_lines(LINES, window_seconds=60)
    key, count = result.busiest_window
    # first three lines fall in 10:00 window
    assert count == 3
    assert "10:00:00" in key


def test_profile_counts_by_window_keys():
    result = profile_lines(LINES, window_seconds=60)
    assert len(result.counts_by_window) == 2


def test_profile_no_timestamped_lines():
    """profile_lines should handle input with no parseable timestamps gracefully."""
    lines = ["no timestamp", "also no timestamp"]
    result = profile_lines(lines)
    assert result.total_lines == 2
    assert result.timestamped_lines == 0
    assert result.duration_seconds == 0.0
    assert result.lines_per_second == 0.0
    assert result.busiest_window == ("", 0)
    assert result.counts_by_window == {}


def test_profile_single_timestamped_line():
    """A single timestamped line should yield zero duration and zero rate."""
    lines = ["2024-01-15 10:00:00 INFO only line"]
    result = profile_lines(lines)
    assert result.total_lines == 1
    assert result.timestamped_lines == 1
    assert result.duration_seconds == pytest.approx(0.0)
    assert result.lines_per_second == 0.0
