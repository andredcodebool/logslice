"""Tests for logslice.tagger."""
from __future__ import annotations

import pytest

from logslice.tagger import (
    TaggedLine,
    TagResult,
    build_tag_rules,
    tag_lines,
)


# ---------------------------------------------------------------------------
# build_tag_rules
# ---------------------------------------------------------------------------

def test_build_tag_rules_empty():
    assert build_tag_rules([]) == []


def test_build_tag_rules_single():
    rules = build_tag_rules(["ERROR=error"])
    assert len(rules) == 1
    label, pat = rules[0]
    assert label == "ERROR"
    assert pat.pattern == "error"


def test_build_tag_rules_multiple():
    rules = build_tag_rules(["E=error", "W=warn"])
    assert [r[0] for r in rules] == ["E", "W"]


def test_build_tag_rules_missing_equals_raises():
    with pytest.raises(ValueError, match="LABEL=PATTERN"):
        build_tag_rules(["NOEQUALSSIGN"])


def test_build_tag_rules_empty_label_raises():
    with pytest.raises(ValueError, match="Empty label"):
        build_tag_rules(["=pattern"])


def test_build_tag_rules_case_insensitive_compile():
    rules = build_tag_rules(["X=Error"])
    _, pat = rules[0]
    assert pat.search("ERROR line") is not None


# ---------------------------------------------------------------------------
# tag_lines
# ---------------------------------------------------------------------------

def test_tag_lines_returns_tag_result():
    result = tag_lines(["hello world"], ["HI=hello"])
    assert isinstance(result, TagResult)


def test_tag_lines_total():
    lines = ["a", "b", "c"]
    result = tag_lines(lines, ["X=a"])
    assert result.total == 3


def test_tag_lines_tagged_count():
    lines = ["error occurred", "all good", "another error"]
    result = tag_lines(lines, ["ERR=error"])
    assert result.tagged_count == 2


def test_tag_lines_unmatched_has_empty_tags():
    result = tag_lines(["nothing here"], ["ERR=error"])
    assert result.lines[0].tags == []


def test_tag_lines_multiple_rules_can_multi_tag():
    result = tag_lines(["error warning line"], ["E=error", "W=warning"])
    assert set(result.lines[0].tags) == {"E", "W"}


def test_tag_lines_lineno_starts_at_one():
    result = tag_lines(["first", "second"], ["X=first"])
    assert result.lines[0].lineno == 1
    assert result.lines[1].lineno == 2


def test_tag_summary_counts():
    lines = ["err1", "err2", "warn1"]
    result = tag_lines(lines, ["E=err", "W=warn"])
    summary = result.tag_summary
    assert summary["E"] == 2
    assert summary["W"] == 1


def test_tagged_line_str_with_tags():
    ln = TaggedLine(lineno=1, text="some error", tags=["ERR"])
    assert str(ln) == "[ERR] some error"


def test_tagged_line_str_no_tags():
    ln = TaggedLine(lineno=1, text="clean line", tags=[])
    assert str(ln) == "clean line"


def test_tagged_line_str_multiple_tags():
    ln = TaggedLine(lineno=1, text="msg", tags=["A", "B"])
    assert str(ln) == "[A,B] msg"


def test_tag_result_stores_rule_patterns():
    result = tag_lines(["x"], ["T=test"])
    assert result.rules == [("T", "test")]


def test_tag_lines_no_rules_no_tags():
    result = tag_lines(["anything"], [])
    assert result.tagged_count == 0
