"""Tests for logslice.summarizer."""
import pytest
from logslice.summarizer import (
    summarize,
    format_summary,
    SummaryResult,
)

SAMPLE_LINES = [
    "2024-01-15T10:00:01 INFO  service started successfully\n",
    "2024-01-15T10:00:02 DEBUG loading configuration file\n",
    "2024-01-15T10:00:03 ERROR failed to connect to database\n",
    "2024-01-15T10:00:04 WARNING retry attempt 1 of 3\n",
    "2024-01-15T10:00:05 ERROR connection timeout exceeded\n",
    "2024-01-15T10:00:06 INFO  reconnected to database\n",
    "2024-01-15T10:00:07 INFO  service running normally\n",
    "no timestamp or level line\n",
]


def test_summarize_returns_summary_result():
    result = summarize(SAMPLE_LINES)
    assert isinstance(result, SummaryResult)


def test_summarize_total_lines():
    result = summarize(SAMPLE_LINES)
    assert result.total_lines == len(SAMPLE_LINES)


def test_summarize_level_counts():
    result = summarize(SAMPLE_LINES)
    assert result.level_counts.get("ERROR") == 2
    assert result.level_counts.get("INFO") == 3
    assert result.level_counts.get("DEBUG") == 1
    assert result.level_counts.get("WARNING") == 1


def test_summarize_first_and_last_timestamp():
    result = summarize(SAMPLE_LINES)
    assert result.first_timestamp == "2024-01-15T10:00:01"
    assert result.last_timestamp == "2024-01-15T10:00:07"


def test_summarize_no_timestamp_lines():
    result = summarize(["no timestamp here\n", "another line\n"])
    assert result.first_timestamp is None
    assert result.last_timestamp is None


def test_summarize_unique_ratio_all_unique():
    result = summarize(SAMPLE_LINES)
    assert result.unique_line_ratio == 1.0


def test_summarize_unique_ratio_with_duplicates():
    lines = ["2024-01-15T10:00:01 INFO same line\n"] * 4
    result = summarize(lines)
    assert result.unique_line_ratio == 0.25


def test_summarize_empty_lines():
    result = summarize([])
    assert result.total_lines == 0
    assert result.level_counts == {}
    assert result.top_tokens == []
    assert result.first_timestamp is None
    assert result.unique_line_ratio == 0.0


def test_summarize_top_tokens_length():
    result = summarize(SAMPLE_LINES, top_n=5)
    assert len(result.top_tokens) <= 5


def test_summarize_top_tokens_are_tuples():
    result = summarize(SAMPLE_LINES)
    for tok, cnt in result.top_tokens:
        assert isinstance(tok, str)
        assert isinstance(cnt, int)


def test_format_summary_contains_total():
    result = summarize(SAMPLE_LINES)
    text = format_summary(result)
    assert "Total lines" in text
    assert str(len(SAMPLE_LINES)) in text


def test_format_summary_contains_levels():
    result = summarize(SAMPLE_LINES)
    text = format_summary(result)
    assert "ERROR" in text
    assert "INFO" in text


def test_format_summary_contains_time_span():
    result = summarize(SAMPLE_LINES)
    text = format_summary(result)
    assert "2024-01-15T10:00:01" in text
    assert "2024-01-15T10:00:07" in text


def test_format_summary_no_timestamps_shows_na():
    result = summarize(["plain line\n"])
    text = format_summary(result)
    assert "n/a" in text
