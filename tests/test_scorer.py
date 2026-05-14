"""Tests for logslice.scorer and logslice.cli_scorer."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.scorer import (
    ScoreResult,
    ScoredLine,
    build_keyword_patterns,
    score_line,
    score_lines,
)
from logslice.cli_scorer import add_scorer_subparser, run_scorer


# ---------------------------------------------------------------------------
# build_keyword_patterns
# ---------------------------------------------------------------------------

def test_build_keyword_patterns_empty():
    assert build_keyword_patterns([]) == []


def test_build_keyword_patterns_compiles():
    pats = build_keyword_patterns(["timeout", "OOM"])
    assert len(pats) == 2
    assert pats[0].search("Connection timeout reached")
    assert pats[1].search("oom killer invoked")  # case-insensitive


# ---------------------------------------------------------------------------
# score_line
# ---------------------------------------------------------------------------

def test_score_line_error_level():
    sl = score_line("2024-01-01 ERROR something broke", [])
    assert sl.score == pytest.approx(0.8)
    assert any("error" in r for r in sl.reasons)


def test_score_line_debug_level():
    sl = score_line("DEBUG entering loop", [])
    assert sl.score == pytest.approx(0.1)


def test_score_line_no_level_no_keywords():
    sl = score_line("plain log message", [])
    assert sl.score == pytest.approx(0.0)
    assert sl.reasons == []


def test_score_line_keyword_adds_weight():
    pats = build_keyword_patterns(["timeout"])
    sl = score_line("INFO connection timeout", pats, keyword_weight=0.3)
    assert sl.score == pytest.approx(min(0.2 + 0.3, 1.0))
    assert any("keyword" in r for r in sl.reasons)


def test_score_line_capped_at_one():
    pats = build_keyword_patterns(["a", "b", "c", "d"])
    sl = score_line("FATAL a b c d", pats, keyword_weight=0.5)
    assert sl.score <= 1.0


def test_score_line_fatal():
    sl = score_line("FATAL disk full", [])
    assert sl.score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# score_lines
# ---------------------------------------------------------------------------

def test_score_lines_returns_score_result():
    result = score_lines(["INFO ok", "ERROR bad"])
    assert isinstance(result, ScoreResult)
    assert result.total == 2


def test_score_lines_above_threshold():
    lines = ["DEBUG low", "ERROR high", "INFO medium"]
    result = score_lines(lines, threshold=0.5)
    above = result.above_threshold
    assert all(sl.score >= 0.5 for sl in above)


def test_score_lines_threshold_zero_returns_all():
    lines = ["a", "b", "c"]
    result = score_lines(lines, threshold=0.0)
    assert len(result.above_threshold) == 3


def test_score_lines_with_keywords():
    lines = ["INFO all good", "INFO timeout occurred"]
    result = score_lines(lines, keywords=["timeout"], keyword_weight=0.4, threshold=0.4)
    assert len(result.above_threshold) == 1
    assert "timeout" in result.above_threshold[0].line


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(
        "DEBUG starting\nINFO ready\nERROR connection refused\nWARN retrying\n",
        encoding="utf-8",
    )
    return p


def _make_args(log_file: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        file=str(log_file),
        keywords=[],
        keyword_weight=0.3,
        threshold=0.0,
        show_score=False,
        top=None,
        func=run_scorer,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_scorer_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_scorer_subparser(sub)
    ns = parser.parse_args(["score", "somefile.log"])
    assert ns.func is run_scorer


def test_run_scorer_basic(log_file: Path, capsys):
    run_scorer(_make_args(log_file))
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_run_scorer_threshold_filters(log_file: Path, capsys):
    run_scorer(_make_args(log_file, threshold=0.7))
    out = capsys.readouterr().out
    assert "ERROR" in out
    assert "DEBUG" not in out


def test_run_scorer_show_score(log_file: Path, capsys):
    run_scorer(_make_args(log_file, threshold=0.5, show_score=True))
    out = capsys.readouterr().out
    for line in out.strip().splitlines():
        assert line.startswith("[")


def test_run_scorer_missing_file(tmp_path: Path):
    ns = _make_args(tmp_path / "missing.log")
    with pytest.raises(SystemExit):
        run_scorer(ns)


def test_run_scorer_top_limits_output(log_file: Path, capsys):
    run_scorer(_make_args(log_file, top=1))
    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 1
