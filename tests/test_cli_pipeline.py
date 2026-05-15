"""Tests for logslice/cli_pipeline.py"""
import argparse
import sys
from pathlib import Path

import pytest

from logslice.cli_pipeline import (
    add_pipeline_subparser,
    run_pipeline,
    _make_grep_stage,
    _make_drop_stage,
    _make_replace_stage,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    f = tmp_path / "app.log"
    f.write_text(
        "INFO  service started\n"
        "ERROR disk full\n"
        "DEBUG heartbeat\n"
        "WARNING low memory\n"
        "ERROR connection refused\n",
        encoding="utf-8",
    )
    return f


def _make_args(log_file: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(file=log_file, grep=[], drop=[], replace=[], stats=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# subparser registration
# ---------------------------------------------------------------------------

def test_add_pipeline_subparser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_pipeline_subparser(sub)
    args = root.parse_args(["pipeline", "/dev/null"])
    assert hasattr(args, "func")


# ---------------------------------------------------------------------------
# stage factories
# ---------------------------------------------------------------------------

def test_make_grep_stage_keeps_matching():
    s = _make_grep_stage(r"ERROR")
    assert s.apply("ERROR disk full") == "ERROR disk full"
    assert s.apply("INFO ok") is None


def test_make_drop_stage_removes_matching():
    s = _make_drop_stage(r"DEBUG")
    assert s.apply("DEBUG heartbeat") is None
    assert s.apply("INFO ok") == "INFO ok"


def test_make_replace_stage_substitutes():
    s = _make_replace_stage("ERROR=CRITICAL")
    assert s.apply("ERROR disk full") == "CRITICAL disk full"


def test_make_replace_stage_invalid_spec_raises():
    with pytest.raises(ValueError, match="FROM=TO"):
        _make_replace_stage("nodivider")


# ---------------------------------------------------------------------------
# run_pipeline output
# ---------------------------------------------------------------------------

def test_run_pipeline_no_stages_prints_all(log_file, capsys):
    run_pipeline(_make_args(log_file))
    out = capsys.readouterr().out
    assert "INFO  service started" in out
    assert "ERROR disk full" in out


def test_run_pipeline_grep_filters(log_file, capsys):
    run_pipeline(_make_args(log_file, grep=["ERROR"]))
    out = capsys.readouterr().out.splitlines()
    assert all("ERROR" in l for l in out)
    assert len(out) == 2


def test_run_pipeline_drop_removes(log_file, capsys):
    run_pipeline(_make_args(log_file, drop=["DEBUG"]))
    out = capsys.readouterr().out
    assert "DEBUG" not in out


def test_run_pipeline_replace_transforms(log_file, capsys):
    run_pipeline(_make_args(log_file, replace=["ERROR=CRITICAL"]))
    out = capsys.readouterr().out
    assert "CRITICAL disk full" in out
    assert "ERROR disk full" not in out


def test_run_pipeline_stats_written_to_stderr(log_file, capsys):
    run_pipeline(_make_args(log_file, grep=["ERROR"], stats=True))
    err = capsys.readouterr().err
    assert "[pipeline]" in err
    assert "dropped=" in err


def test_run_pipeline_missing_file_exits(tmp_path):
    missing = tmp_path / "nope.log"
    with pytest.raises(SystemExit):
        run_pipeline(_make_args(missing))
