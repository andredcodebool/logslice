"""Tests for logslice.cli_alerter."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

from logslice.cli_alerter import add_alerter_subparser, run_alerter


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(
        "2024-01-01 INFO  startup\n"
        "2024-01-01 ERROR disk full\n"
        "2024-01-01 DEBUG heartbeat\n"
        "2024-01-01 ERROR oom\n",
        encoding="utf-8",
    )
    return p


def _make_args(log_file: Path, rules=None, summary=False, exit_code=False):
    ns = argparse.Namespace(
        file=str(log_file),
        rules=rules or ["ERR=ERROR"],
        summary=summary,
        exit_code=exit_code,
    )
    return ns


def test_add_alerter_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_alerter_subparser(sub)
    args = parser.parse_args(["alert", "some.log", "-r", "X=foo"])
    assert hasattr(args, "func")


def test_run_alerter_prints_hits(log_file, capsys):
    run_alerter(_make_args(log_file))
    out = capsys.readouterr().out
    assert "[ERR]" in out


def test_run_alerter_summary_line(log_file, capsys):
    run_alerter(_make_args(log_file))
    out = capsys.readouterr().out
    assert "alert summary" in out


def test_run_alerter_summary_only_no_hits_printed(log_file, capsys):
    run_alerter(_make_args(log_file, summary=True))
    out = capsys.readouterr().out
    assert "[ERR]" not in out
    assert "alert summary" in out


def test_run_alerter_missing_file_exits(tmp_path):
    ns = _make_args(tmp_path / "missing.log")
    with pytest.raises(SystemExit) as exc_info:
        run_alerter(ns)
    assert exc_info.value.code == 2


def test_run_alerter_no_rules_exits(log_file):
    ns = _make_args(log_file, rules=[])
    with pytest.raises(SystemExit) as exc_info:
        run_alerter(ns)
    assert exc_info.value.code == 2


def test_run_alerter_exit_code_on_hits(log_file):
    ns = _make_args(log_file, exit_code=True)
    with pytest.raises(SystemExit) as exc_info:
        run_alerter(ns)
    assert exc_info.value.code == 1


def test_run_alerter_no_exit_code_when_no_hits(log_file, capsys):
    ns = _make_args(log_file, rules=["CRIT=CRITICAL"], exit_code=True)
    run_alerter(ns)  # should not raise
    out = capsys.readouterr().out
    assert "0/4" in out
