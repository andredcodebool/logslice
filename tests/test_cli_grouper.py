"""Tests for logslice.cli_grouper."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.cli_grouper import add_grouper_subparser, run_grouper


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text(
        "2024-06-01 12:00:05 ERROR boom\n"
        "2024-06-01 12:00:10 INFO  ok\n"
        "2024-06-01 12:01:05 ERROR again\n"
        "no timestamp here\n"
    )
    return p


def _make_args(log_file: Path, **kwargs) -> argparse.Namespace:
    defaults = {
        "file": str(log_file),
        "pattern": None,
        "window": None,
        "show_ungrouped": False,
        "func": run_grouper,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_grouper_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_grouper_subparser(sub)
    args = parser.parse_args(["group", "myfile.log", "--pattern", "(ERROR)"])
    assert args.pattern == "(ERROR)"


def test_run_grouper_pattern_prints_groups(capsys, log_file):
    args = _make_args(log_file, pattern=r"(ERROR|INFO)")
    run_grouper(args)
    out = capsys.readouterr().out
    assert "ERROR" in out
    assert "INFO" in out


def test_run_grouper_window_prints_groups(capsys, log_file):
    args = _make_args(log_file, window=60)
    run_grouper(args)
    out = capsys.readouterr().out
    assert "2024-06-01" in out


def test_run_grouper_show_ungrouped(capsys, log_file):
    args = _make_args(log_file, pattern=r"(ERROR|INFO)", show_ungrouped=True)
    run_grouper(args)
    out = capsys.readouterr().out
    assert "ungrouped" in out


def test_run_grouper_missing_file_exits(tmp_path):
    args = _make_args(tmp_path / "nope.log", pattern=r"(ERROR)")
    with pytest.raises(SystemExit):
        run_grouper(args)


def test_run_grouper_summary_line(capsys, log_file):
    args = _make_args(log_file, pattern=r"(ERROR|INFO)")
    run_grouper(args)
    out = capsys.readouterr().out
    assert "[group]" in out
    assert "groups" in out
