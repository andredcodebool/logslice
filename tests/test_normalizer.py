"""Tests for logslice.normalizer and logslice.cli_normalizer."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.normalizer import (
    NormalizeResult,
    build_rules,
    normalize_line,
    normalize_lines,
)
from logslice.cli_normalizer import add_normalizer_subparser, run_normalizer


# ---------------------------------------------------------------------------
# build_rules
# ---------------------------------------------------------------------------

def test_build_rules_empty_returns_empty():
    assert build_rules([]) == []


def test_build_rules_unknown_raises():
    with pytest.raises(ValueError, match="Unknown built-in rule"):
        build_rules(["nonexistent"])


def test_build_rules_builtin_timestamp():
    rules = build_rules(["timestamp"])
    assert len(rules) == 1


def test_build_rules_custom_valid():
    rules = build_rules([], custom=["foo=<BAR>"])
    assert len(rules) == 1


def test_build_rules_custom_missing_equals_raises():
    with pytest.raises(ValueError, match="Custom rule must be"):
        build_rules([], custom=["noequalssign"])


# ---------------------------------------------------------------------------
# normalize_line
# ---------------------------------------------------------------------------

def test_normalize_line_timestamp():
    rules = build_rules(["timestamp"])
    result = normalize_line("2024-01-15T12:34:56Z INFO started", rules)
    assert "<TS>" in result
    assert "2024" not in result


def test_normalize_line_ipv4():
    rules = build_rules(["ipv4"])
    result = normalize_line("connection from 192.168.1.42 accepted", rules)
    assert "<IP>" in result
    assert "192.168" not in result


def test_normalize_line_uuid():
    rules = build_rules(["uuid"])
    line = "request id=550e8400-e29b-41d4-a716-446655440000 done"
    result = normalize_line(line, rules)
    assert "<UUID>" in result


def test_normalize_line_no_rules_unchanged():
    line = "plain log line"
    assert normalize_line(line, []) == line


# ---------------------------------------------------------------------------
# normalize_lines
# ---------------------------------------------------------------------------

def test_normalize_lines_returns_result():
    lines = ["2024-01-01T00:00:00Z INFO hello\n"]
    result = normalize_lines(lines, builtin_rules=["timestamp"])
    assert isinstance(result, NormalizeResult)


def test_normalize_lines_total():
    lines = ["line one\n", "line two\n"]
    result = normalize_lines(lines)
    assert result.total == 2


def test_normalize_lines_changed_count():
    lines = ["2024-01-01T00:00:00Z INFO msg\n", "plain line\n"]
    result = normalize_lines(lines, builtin_rules=["timestamp"])
    assert result.changed_count == 1


def test_normalize_lines_no_rules_zero_changed():
    lines = ["unchanged\n", "also unchanged\n"]
    result = normalize_lines(lines)
    assert result.changed_count == 0


def test_normalize_lines_rules_applied_recorded():
    result = normalize_lines(["x\n"], builtin_rules=["uuid", "ipv4"])
    assert "uuid" in result.rules_applied
    assert "ipv4" in result.rules_applied


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text(
        "2024-03-10T08:00:00Z ERROR connect from 10.0.0.1 failed\n"
        "plain message\n",
        encoding="utf-8",
    )
    return p


def _make_args(log_file: Path, **kwargs) -> argparse.Namespace:
    defaults = {
        "file": str(log_file),
        "rules": [],
        "custom": [],
        "stats": False,
        "inplace": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_normalizer_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_normalizer_subparser(subs)
    args = parser.parse_args(["normalize", "somefile.log"])
    assert args.func is run_normalizer


def test_run_normalizer_outputs_normalized(log_file: Path, capsys):
    args = _make_args(log_file, rules=["timestamp", "ipv4"])
    run_normalizer(args)
    out = capsys.readouterr().out
    assert "<TS>" in out
    assert "<IP>" in out


def test_run_normalizer_inplace(log_file: Path):
    args = _make_args(log_file, rules=["timestamp"], inplace=True)
    run_normalizer(args)
    content = log_file.read_text(encoding="utf-8")
    assert "<TS>" in content


def test_run_normalizer_missing_file_exits(tmp_path: Path):
    args = _make_args(tmp_path / "ghost.log")
    with pytest.raises(SystemExit):
        run_normalizer(args)


def test_run_normalizer_bad_rule_exits(log_file: Path):
    args = _make_args(log_file, rules=["not_a_rule"])
    with pytest.raises(SystemExit):
        run_normalizer(args)
