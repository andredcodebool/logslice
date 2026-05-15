"""Tests for logslice.grouper."""
from __future__ import annotations

import pytest

from logslice.grouper import GroupResult, group_by_pattern, group_by_window


LINES_LEVEL = [
    "2024-01-01T10:00:00 ERROR something broke",
    "2024-01-01T10:00:01 INFO  all good",
    "2024-01-01T10:00:02 ERROR another failure",
    "2024-01-01T10:00:03 DEBUG verbose stuff",
    "no timestamp or level here",
]


# ---------------------------------------------------------------------------
# group_by_pattern
# ---------------------------------------------------------------------------

def test_group_by_pattern_returns_group_result():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert isinstance(result, GroupResult)


def test_group_by_pattern_correct_keys():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert "ERROR" in result.groups
    assert "INFO" in result.groups
    assert "DEBUG" in result.groups


def test_group_by_pattern_counts():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert len(result.groups["ERROR"]) == 2
    assert len(result.groups["INFO"]) == 1


def test_group_by_pattern_ungrouped():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert len(result.ungrouped) == 1
    assert result.ungrouped[0] == "no timestamp or level here"


def test_group_by_pattern_total():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert result.total == len(LINES_LEVEL)


def test_group_by_pattern_group_count():
    result = group_by_pattern(LINES_LEVEL, r"(ERROR|INFO|DEBUG|WARN)")
    assert result.group_count == 3


def test_group_by_pattern_invalid_regex_raises():
    with pytest.raises(ValueError, match="Invalid grouping pattern"):
        group_by_pattern(LINES_LEVEL, r"(unclosed")


def test_group_by_pattern_no_capture_group_uses_full_match():
    lines = ["alpha beta", "gamma delta", "alpha gamma"]
    result = group_by_pattern(lines, r"alpha")
    assert "alpha" in result.groups
    assert len(result.groups["alpha"]) == 2


# ---------------------------------------------------------------------------
# group_by_window
# ---------------------------------------------------------------------------

WINDOW_LINES = [
    "2024-06-01 12:00:05 INFO  first",
    "2024-06-01 12:00:45 INFO  second",
    "2024-06-01 12:01:10 INFO  third",
    "not a timestamped line",
]


def test_group_by_window_returns_group_result():
    result = group_by_window(WINDOW_LINES, window_seconds=60)
    assert isinstance(result, GroupResult)


def test_group_by_window_separates_minutes():
    result = group_by_window(WINDOW_LINES, window_seconds=60)
    assert result.group_count == 2


def test_group_by_window_ungrouped_no_timestamp():
    result = group_by_window(WINDOW_LINES, window_seconds=60)
    assert len(result.ungrouped) == 1


def test_group_by_window_total():
    result = group_by_window(WINDOW_LINES, window_seconds=60)
    assert result.total == len(WINDOW_LINES)


def test_group_by_window_invalid_window_raises():
    with pytest.raises(ValueError, match="positive"):
        group_by_window(WINDOW_LINES, window_seconds=0)


def test_group_by_window_large_window_one_group():
    result = group_by_window(WINDOW_LINES, window_seconds=3600)
    assert result.group_count == 1
