"""Tests for logslice.cli_tracer."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.cli_tracer import add_tracer_subparser, run_tracer


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(
        "2024-01-01 req_id=aaa INFO  start\n"
        "2024-01-01 req_id=bbb DEBUG init\n"
        "2024-01-01 req_id=aaa ERROR crash\n",
        encoding="utf-8",
    )
    return p


def _make_args(log_file: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        file=str(log_file),
        pattern=r"req_id=(\S+)",
        token=None,
        summary=False,
        func=run_tracer,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_tracer_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_tracer_subparser(subs)
    parsed = parser.parse_args(
        ["trace", "somefile.log", "--pattern", r"id=(\S+)"]
    )
    assert parsed.func is run_tracer


def test_run_tracer_prints_groups(log_file: Path, capsys):
    args = _make_args(log_file)
    run_tracer(args)
    out = capsys.readouterr().out
    assert "aaa" in out
    assert "bbb" in out


def test_run_tracer_token_filter(log_file: Path, capsys):
    args = _make_args(log_file, token="aaa")
    run_tracer(args)
    out = capsys.readouterr().out
    assert "aaa" in out
    assert "bbb" not in out


def test_run_tracer_summary_flag(log_file: Path, capsys):
    args = _make_args(log_file, summary=True)
    run_tracer(args)
    out = capsys.readouterr().out
    assert "tokens=" in out
    assert "scanned=" in out


def test_run_tracer_missing_file(tmp_path: Path, capsys):
    args = _make_args(tmp_path / "missing.log")
    with pytest.raises(SystemExit) as exc:
        run_tracer(args)
    assert exc.value.code == 1
    assert "not found" in capsys.readouterr().err


def test_run_tracer_no_tokens_stderr(log_file: Path, capsys):
    args = _make_args(log_file, token="zzz")
    run_tracer(args)
    err = capsys.readouterr().err
    assert "no tokens" in err
