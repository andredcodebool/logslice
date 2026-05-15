"""Tests for logslice.alerter."""
from __future__ import annotations

import pytest

from logslice.alerter import (
    AlertHit,
    AlertResult,
    AlertRule,
    build_rules,
    check_alerts,
)


# ---------------------------------------------------------------------------
# build_rules
# ---------------------------------------------------------------------------

def test_build_rules_empty():
    assert build_rules([]) == []


def test_build_rules_single():
    rules = build_rules(["OOM=out of memory"])
    assert len(rules) == 1
    assert rules[0].label == "OOM"
    assert rules[0].pattern.pattern == "out of memory"
    assert rules[0].level is None


def test_build_rules_with_level():
    rules = build_rules(["CRIT=disk full:ERROR"])
    assert rules[0].level == "ERROR"
    assert rules[0].pattern.pattern == "disk full"


def test_build_rules_missing_equals_raises():
    with pytest.raises(ValueError, match="missing '='"):
        build_rules(["BAD_RULE"])


def test_build_rules_empty_label_raises():
    with pytest.raises(ValueError, match="label is empty"):
        build_rules(["=pattern"])


def test_build_rules_multiple():
    rules = build_rules(["A=foo", "B=bar"])
    assert [r.label for r in rules] == ["A", "B"]


# ---------------------------------------------------------------------------
# check_alerts
# ---------------------------------------------------------------------------

LINES = [
    "2024-01-01 INFO  service started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 DEBUG ping\n",
    "2024-01-01 ERROR out of memory\n",
    "2024-01-01 WARN  slow query\n",
]


def test_check_alerts_returns_alert_result():
    rules = build_rules(["ANY=ERROR"])
    result = check_alerts(LINES, rules)
    assert isinstance(result, AlertResult)


def test_check_alerts_total():
    rules = build_rules(["ANY=ERROR"])
    result = check_alerts(LINES, rules)
    assert result.total == len(LINES)


def test_check_alerts_hit_count():
    rules = build_rules(["ERR=ERROR"])
    result = check_alerts(LINES, rules)
    assert result.hit_count == 2


def test_check_alerts_no_hits():
    rules = build_rules(["CRIT=CRITICAL"])
    result = check_alerts(LINES, rules)
    assert result.hit_count == 0


def test_check_alerts_hit_line_numbers():
    rules = build_rules(["ERR=ERROR"])
    result = check_alerts(LINES, rules)
    assert [h.line_no for h in result.hits] == [2, 4]


def test_check_alerts_hit_rate():
    rules = build_rules(["ERR=ERROR"])
    result = check_alerts(LINES, rules)
    assert abs(result.hit_rate - 2 / 5) < 1e-9


def test_check_alerts_hit_rate_empty():
    result = check_alerts([], build_rules(["X=foo"]))
    assert result.hit_rate == 0.0


def test_check_alerts_level_filter_matches():
    rules = build_rules(["ERR=disk full:ERROR"])
    result = check_alerts(LINES, rules)
    assert result.hit_count == 1
    assert result.hits[0].line_no == 2


def test_check_alerts_level_filter_no_match():
    rules = build_rules(["WARN_DISK=disk full:WARN"])
    result = check_alerts(LINES, rules)
    assert result.hit_count == 0


def test_alert_hit_str():
    hit = AlertHit(line_no=3, line="ERROR something bad\n", rule_label="BAD")
    assert "[BAD]" in str(hit)
    assert "line 3" in str(hit)
