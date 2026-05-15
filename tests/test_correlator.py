"""Tests for logslice.correlator."""
from __future__ import annotations

import pytest

from logslice.correlator import (
    CorrelateResult,
    CorrelatedGroup,
    correlate,
    format_correlation,
    group_count,
    total,
)

PATTERN = r"req=(?P<token>[\w-]+)"


def _src(label: str, *lines: str):
    return (label, list(lines))


# ---------------------------------------------------------------------------
# correlate()
# ---------------------------------------------------------------------------

def test_correlate_returns_correlate_result():
    result = correlate([], PATTERN)
    assert isinstance(result, CorrelateResult)


def test_correlate_single_source_single_token():
    result = correlate([_src("a", "req=abc hello")], PATTERN)
    assert "abc" in result.groups


def test_correlate_groups_same_token():
    result = correlate(
        [_src("a", "req=abc first", "req=abc second")],
        PATTERN,
    )
    assert len(result.groups["abc"]) == 2


def test_correlate_different_tokens_separate_groups():
    result = correlate(
        [_src("a", "req=abc line", "req=xyz line")],
        PATTERN,
    )
    assert set(result.groups.keys()) == {"abc", "xyz"}


def test_correlate_unmatched_lines_collected():
    result = correlate([_src("a", "no token here", "req=abc ok")], PATTERN)
    assert len(result.unmatched) == 1
    assert result.unmatched[0] == ("a", "no token here")


def test_correlate_multiple_sources():
    result = correlate(
        [
            _src("app", "req=abc start"),
            _src("db", "req=abc query"),
        ],
        PATTERN,
    )
    sources = [src for src, _ in result.groups["abc"].lines]
    assert "app" in sources
    assert "db" in sources


def test_correlate_invalid_pattern_raises():
    with pytest.raises(ValueError, match="token"):
        correlate([_src("a", "line")], r"req=([\w-]+)")


# ---------------------------------------------------------------------------
# total() / group_count()
# ---------------------------------------------------------------------------

def test_total_includes_unmatched():
    result = correlate(
        [_src("a", "req=abc ok", "no token")],
        PATTERN,
    )
    assert total(result) == 2


def test_group_count_correct():
    result = correlate(
        [_src("a", "req=abc ok", "req=xyz ok", "req=abc again")],
        PATTERN,
    )
    assert group_count(result) == 2


def test_total_empty_sources():
    result = correlate([], PATTERN)
    assert total(result) == 0


# ---------------------------------------------------------------------------
# format_correlation()
# ---------------------------------------------------------------------------

def test_format_correlation_contains_token():
    result = correlate([_src("a", "req=abc hello")], PATTERN)
    output = format_correlation(result)
    assert "abc" in output


def test_format_correlation_hides_unmatched_by_default():
    result = correlate([_src("a", "no token")], PATTERN)
    output = format_correlation(result)
    assert "unmatched" not in output


def test_format_correlation_shows_unmatched_when_requested():
    result = correlate([_src("a", "no token")], PATTERN)
    output = format_correlation(result, show_unmatched=True)
    assert "unmatched" in output


def test_format_correlation_source_label_present():
    result = correlate([_src("myapp", "req=abc hello")], PATTERN)
    output = format_correlation(result)
    assert "myapp" in output
