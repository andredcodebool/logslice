"""Tests for logslice.context — context-lines extraction and formatting."""

import pytest
from logslice.context import extract_with_context, format_context_block


LINES = [
    "line 0\n",
    "line 1\n",
    "line 2\n",
    "line 3\n",
    "line 4\n",
    "line 5\n",
    "line 6\n",
]


# ---------------------------------------------------------------------------
# extract_with_context
# ---------------------------------------------------------------------------

def test_no_matches_returns_empty():
    result = extract_with_context(LINES, [], before=2, after=2)
    assert result == []


def test_match_only_no_context():
    result = extract_with_context(LINES, [3], before=0, after=0)
    assert result == [(3, "line 3\n", True)]


def test_before_context():
    result = extract_with_context(LINES, [3], before=2, after=0)
    indices = [r[0] for r in result]
    assert indices == [1, 2, 3]
    # only index 3 is the actual match
    assert result[2][2] is True
    assert result[0][2] is False
    assert result[1][2] is False


def test_after_context():
    result = extract_with_context(LINES, [3], before=0, after=2)
    indices = [r[0] for r in result]
    assert indices == [3, 4, 5]
    assert result[0][2] is True


def test_before_and_after_context():
    result = extract_with_context(LINES, [3], before=1, after=1)
    indices = [r[0] for r in result]
    assert indices == [2, 3, 4]


def test_context_clamped_at_boundaries():
    # match at index 0 — no lines before
    result = extract_with_context(LINES, [0], before=3, after=0)
    assert result[0][0] == 0
    assert len(result) == 1

    # match at last index — no lines after
    last = len(LINES) - 1
    result = extract_with_context(LINES, [last], before=0, after=3)
    assert result[-1][0] == last
    assert len(result) == 1


def test_overlapping_contexts_deduplicated():
    # matches at 2 and 4 with after=2 each — index 4,5,6 and 2,3,4
    result = extract_with_context(LINES, [2, 4], before=0, after=2)
    indices = [r[0] for r in result]
    # should not have duplicates
    assert len(indices) == len(set(indices))
    assert sorted(indices) == indices  # sorted


def test_match_flag_preserved_when_also_context():
    # index 3 is both a match AND context-after of index 2
    result = extract_with_context(LINES, [2, 3], before=0, after=1)
    entry_3 = next(r for r in result if r[0] == 3)
    assert entry_3[2] is True  # match wins over context flag


# ---------------------------------------------------------------------------
# format_context_block
# ---------------------------------------------------------------------------

def test_format_no_separator_for_contiguous():
    entries = [(0, "a\n", True), (1, "b\n", False), (2, "c\n", True)]
    output = format_context_block(entries)
    assert "--" not in output
    assert output == ["a", "b", "c"]


def test_format_separator_between_gaps():
    entries = [(0, "a\n", True), (5, "f\n", True)]
    output = format_context_block(entries)
    assert "--" in output
    assert output[0] == "a"
    assert output[-1] == "f"


def test_format_multiple_gaps_have_multiple_separators():
    """Each non-contiguous group of entries should be separated by '--'."""
    entries = [
        (0, "a\n", True),
        (5, "f\n", False),
        (10, "k\n", True),
    ]
    output = format_context_block(entries)
    separator_count = output.count("--")
    assert separator_count == 2
    assert output[0] == "a"
    assert output[-1] == "k"


def test_format_strips_trailing_newline():
    """Lines in the output should have their trailing newline stripped."""
    entries = [(0, "hello\n", True), (1, "world\n", False)]
    output = format_context_block(entries)
    assert all(not line.endswith("\n") for line in output if line != "--")
