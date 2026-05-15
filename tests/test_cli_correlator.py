"""Tests for logslice.cli_correlator."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from logslice.cli_correlator import add_correlator_subparser, run_correlator


@pytest.fixture()
def log_files(tmp_path: Path):
    """Two small log files sharing a request token."""
    a = tmp_path / "app.log"
    b = tmp_path / "db.log"
    a.write_text(
        textwrap.dedent("""\
            req=abc INFO start
            req=xyz INFO other
            no token line
        """)
    )
    b.write_text(
        textwrap.dedent("""\
            req=abc DEBUG query
            req=abc DEBUG result
        """)
    )
    return a, b


def _make_args(files, pattern, summary=False, show_unmatched=False):
    ns = argparse.Namespace(
        files=[str(f) for f in files],
        pattern=pattern,
        summary=summary,
        show_unmatched=show_unmatched,
        func=run_correlator,
    )
    return ns


def test_add_correlator_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_correlator_subparser(sub)
    args = parser.parse_args(["correlate", "--pattern", "(?P<token>x)", "f.log"])
    assert hasattr(args, "func")


def test_run_correlator_prints_groups(log_files, capsys):
    a, b = log_files
    args = _make_args([a, b], r"req=(?P<token>[\w-]+)")
    run_correlator(args)
    out = capsys.readouterr().out
    assert "abc" in out
    assert "xyz" in out


def test_run_correlator_summary_flag(log_files, capsys):
    a, b = log_files
    args = _make_args([a, b], r"req=(?P<token>[\w-]+)", summary=True)
    run_correlator(args)
    out = capsys.readouterr().out
    assert "groups" in out
    assert "total" in out


def test_run_correlator_show_unmatched(log_files, capsys):
    a, b = log_files
    args = _make_args([a, b], r"req=(?P<token>[\w-]+)", show_unmatched=True)
    run_correlator(args)
    out = capsys.readouterr().out
    assert "unmatched" in out


def test_run_correlator_bad_pattern_exits(log_files):
    a, _ = log_files
    args = _make_args([a], r"req=([\w-]+)")
    with pytest.raises(SystemExit):
        run_correlator(args)


def test_run_correlator_label_syntax(log_files, capsys):
    a, b = log_files
    labeled_a = f"frontend={a}"
    labeled_b = f"backend={b}"
    args = _make_args([labeled_a, labeled_b], r"req=(?P<token>[\w-]+)")
    run_correlator(args)
    out = capsys.readouterr().out
    assert "frontend" in out
    assert "backend" in out
