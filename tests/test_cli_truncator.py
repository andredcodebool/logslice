"""Tests for logslice.cli_truncator."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.cli_truncator import add_truncator_subparser, run_truncator


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.log"
    f.write_text("\n".join(f"line {i}" for i in range(1, 31)))
    return f


def _make_args(file: str, limit: int = 10, mode: str = "head", no_summary: bool = False):
    ns = argparse.Namespace(file=file, limit=limit, mode=mode, no_summary=no_summary)
    return ns


def test_add_truncator_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_truncator_subparser(sub)
    args = parser.parse_args(["truncate", "myfile.log", "--limit", "5"])
    assert args.limit == 5
    assert args.mode == "head"


def test_run_truncator_head_prints_first_lines(log_file: Path, capsys):
    args = _make_args(str(log_file), limit=5, mode="head", no_summary=True)
    run_truncator(args)
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "line 1"
    assert out[-1] == "line 5"
    assert len(out) == 5


def test_run_truncator_tail_prints_last_lines(log_file: Path, capsys):
    args = _make_args(str(log_file), limit=5, mode="tail", no_summary=True)
    run_truncator(args)
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1] == "line 30"
    assert len(out) == 5


def test_run_truncator_middle_contains_placeholder(log_file: Path, capsys):
    args = _make_args(str(log_file), limit=6, mode="middle", no_summary=True)
    run_truncator(args)
    out = capsys.readouterr().out
    assert "omitted" in out


def test_run_truncator_summary_written_to_stderr(log_file: Path, capsys):
    args = _make_args(str(log_file), limit=5, mode="head", no_summary=False)
    run_truncator(args)
    err = capsys.readouterr().err
    assert "truncate" in err
    assert "omitted" in err


def test_run_truncator_no_summary_flag(log_file: Path, capsys):
    args = _make_args(str(log_file), limit=5, mode="head", no_summary=True)
    run_truncator(args)
    err = capsys.readouterr().err
    assert err == ""


def test_run_truncator_missing_file_exits(tmp_path: Path):
    args = _make_args(str(tmp_path / "ghost.log"))
    with pytest.raises(SystemExit) as exc_info:
        run_truncator(args)
    assert exc_info.value.code == 1
