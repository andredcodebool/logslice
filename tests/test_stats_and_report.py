"""Tests for logslice.stats and logslice.report."""
import json
import pytest

from logslice.stats import LogStats, extract_level, compute_stats
from logslice.report import format_stats_text, format_stats_json, _level_bar


SAMPLE_LINES = [
    "2024-01-15 10:00:00 INFO  Service started",
    "2024-01-15 10:01:00 DEBUG Loaded config",
    "2024-01-15 10:02:00 WARNING Disk usage high",
    "2024-01-15 10:03:00 ERROR  Connection refused",
    "2024-01-15 10:04:00 INFO  Retrying",
    "2024-01-15 10:05:00 CRITICAL Out of memory",
]


# --- extract_level ---

def test_extract_level_info():
    assert extract_level("2024-01-15 10:00:00 INFO Service started") == "INFO"


def test_extract_level_error():
    assert extract_level("ERROR: something went wrong") == "ERROR"


def test_extract_level_case_insensitive():
    assert extract_level("[warning] disk full") == "WARNING"


def test_extract_level_none():
    assert extract_level("no level keyword here") is None


# --- compute_stats ---

def test_compute_stats_counts():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    assert stats.total_lines == 6
    assert stats.matched_lines == 6


def test_compute_stats_level_breakdown():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    assert stats.level_counts["INFO"] == 2
    assert stats.level_counts["ERROR"] == 1
    assert stats.level_counts["CRITICAL"] == 1


def test_compute_stats_error_count():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    assert stats.error_count == 2  # ERROR + CRITICAL


def test_compute_stats_warning_count():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    assert stats.warning_count == 1


def test_compute_stats_timestamps_present():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    assert stats.first_timestamp is not None
    assert stats.last_timestamp is not None


def test_compute_stats_empty_matched():
    stats = compute_stats(SAMPLE_LINES, [])
    assert stats.matched_lines == 0
    assert stats.total_lines == 6
    assert stats.first_timestamp is None


# --- LogStats.as_dict ---

def test_as_dict_keys():
    stats = LogStats(total_lines=10, matched_lines=5)
    d = stats.as_dict()
    assert "total_lines" in d
    assert "matched_lines" in d
    assert "level_counts" in d
    assert "error_count" in d


# --- format_stats_text ---

def test_format_stats_text_contains_totals():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES)
    report = format_stats_text(stats)
    assert "6" in report
    assert "Log Statistics" in report


def test_format_stats_text_custom_title():
    stats = LogStats(total_lines=3, matched_lines=1)
    report = format_stats_text(stats, title="My Report")
    assert "My Report" in report


# --- format_stats_json ---

def test_format_stats_json_valid():
    stats = compute_stats(SAMPLE_LINES, SAMPLE_LINES[:3])
    raw = format_stats_json(stats)
    parsed = json.loads(raw)
    assert parsed["total_lines"] == 6
    assert parsed["matched_lines"] == 3


# --- _level_bar ---

def test_level_bar_full():
    bar = _level_bar(20, 20)
    assert "#" in bar


def test_level_bar_zero_total():
    assert _level_bar(5, 0) == ""
