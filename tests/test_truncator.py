"""Tests for logslice.truncator."""

from __future__ import annotations

import pytest

from logslice.truncator import (
    TruncateResult,
    _removed,
    truncate_head,
    truncate_lines,
    truncate_middle,
    truncate_tail,
)

LINES = [f"line {i}" for i in range(1, 21)]  # 20 lines


# ---------------------------------------------------------------------------
# truncate_head
# ---------------------------------------------------------------------------

def test_head_keeps_first_n():
    r = truncate_head(LINES, 5)
    assert r.lines == LINES[:5]


def test_head_mode_label():
    r = truncate_head(LINES, 3)
    assert r.mode == "head"


def test_head_counts():
    r = truncate_head(LINES, 7)
    assert r.original_count == 20
    assert r.truncated_count == 7
    assert _removed(r) == 13


def test_head_no_truncation_when_limit_exceeds_length():
    r = truncate_head(LINES, 100)
    assert r.lines == LINES
    assert r.truncated_count == 20


def test_head_invalid_limit_raises():
    with pytest.raises(ValueError):
        truncate_head(LINES, 0)


# ---------------------------------------------------------------------------
# truncate_tail
# ---------------------------------------------------------------------------

def test_tail_keeps_last_n():
    r = truncate_tail(LINES, 5)
    assert r.lines == LINES[-5:]


def test_tail_mode_label():
    r = truncate_tail(LINES, 3)
    assert r.mode == "tail"


def test_tail_counts():
    r = truncate_tail(LINES, 4)
    assert r.original_count == 20
    assert r.truncated_count == 4


def test_tail_invalid_limit_raises():
    with pytest.raises(ValueError):
        truncate_tail(LINES, -1)


# ---------------------------------------------------------------------------
# truncate_middle
# ---------------------------------------------------------------------------

def test_middle_omits_centre():
    r = truncate_middle(LINES, 6)
    # 3 head + placeholder + 3 tail = 7 items in .lines
    assert r.lines[0] == "line 1"
    assert r.lines[-1] == "line 20"
    assert any("omitted" in l for l in r.lines)


def test_middle_truncated_count():
    r = truncate_middle(LINES, 6)
    assert r.truncated_count == 6


def test_middle_no_truncation_when_small():
    short = LINES[:4]
    r = truncate_middle(short, 10)
    assert r.lines == short
    assert _removed(r) == 0


def test_middle_invalid_limit_raises():
    with pytest.raises(ValueError):
        truncate_middle(LINES, 0)


# ---------------------------------------------------------------------------
# truncate_lines dispatcher
# ---------------------------------------------------------------------------

def test_dispatch_head():
    r = truncate_lines(LINES, 5, mode="head")
    assert r.mode == "head"


def test_dispatch_tail():
    r = truncate_lines(LINES, 5, mode="tail")
    assert r.mode == "tail"


def test_dispatch_middle():
    r = truncate_lines(LINES, 8, mode="middle")
    assert r.mode == "middle"


def test_dispatch_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown mode"):
        truncate_lines(LINES, 5, mode="random")
