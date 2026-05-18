"""Tests for logslice.tracer."""
from __future__ import annotations

import pytest

from logslice.tracer import (
    TraceGroup,
    TraceResult,
    _extract_tokens,
    format_trace,
    trace_lines,
)

IMPORT RE = __import__("re")

SAMPLE = [
    "2024-01-01 req_id=abc INFO  user login",
    "2024-01-01 req_id=xyz DEBUG fetching data",
    "2024-01-01 req_id=abc ERROR  timeout",
    "2024-01-01 no-token here",
    "2024-01-01 req_id=xyz INFO  done",
]

PATTERN = r"req_id=(\S+)"


def test_extract_tokens_finds_match():
    import re
    compiled = re.compile(r"req_id=(\S+)")
    tokens = _extract_tokens("req_id=abc INFO req_id=abc again", compiled)
    # deduped
    assert tokens == ["abc"]


def test_extract_tokens_no_match():
    import re
    compiled = re.compile(r"req_id=(\S+)")
    assert _extract_tokens("no token here", compiled) == []


def test_trace_lines_returns_trace_result():
    result = trace_lines(SAMPLE, PATTERN)
    assert isinstance(result, TraceResult)


def test_trace_lines_total_scanned():
    result = trace_lines(SAMPLE, PATTERN)
    assert result.total_scanned == len(SAMPLE)


def test_trace_lines_token_count():
    result = trace_lines(SAMPLE, PATTERN)
    assert result.token_count == 2


def test_trace_lines_correct_groups():
    result = trace_lines(SAMPLE, PATTERN)
    assert "abc" in result.groups
    assert "xyz" in result.groups


def test_trace_lines_group_line_counts():
    result = trace_lines(SAMPLE, PATTERN)
    assert len(result.groups["abc"]) == 2
    assert len(result.groups["xyz"]) == 2


def test_trace_lines_total_matched():
    result = trace_lines(SAMPLE, PATTERN)
    assert result.total_matched == 4


def test_trace_lines_token_filter():
    result = trace_lines(SAMPLE, PATTERN, token_filter="abc")
    assert result.token_count == 1
    assert "abc" in result.groups
    assert "xyz" not in result.groups


def test_trace_lines_token_filter_no_match():
    result = trace_lines(SAMPLE, PATTERN, token_filter="nonexistent")
    assert result.token_count == 0
    assert result.total_matched == 0


def test_format_trace_contains_token():
    result = trace_lines(SAMPLE, PATTERN)
    output = format_trace(result)
    assert "abc" in output
    assert "xyz" in output


def test_format_trace_contains_lines():
    result = trace_lines(SAMPLE, PATTERN, token_filter="abc")
    output = format_trace(result)
    assert "user login" in output
    assert "timeout" in output


def test_format_trace_summary_flag():
    result = trace_lines(SAMPLE, PATTERN)
    output = format_trace(result, show_counts=True)
    assert "tokens=" in output
    assert "scanned=" in output


def test_format_trace_empty_result():
    result = TraceResult()
    assert format_trace(result) == ""
