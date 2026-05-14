"""Tests for logslice.cli_tagger."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from logslice.cli_tagger import add_tagger_subparser, run_tagger


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        2024-01-01 INFO  service started
        2024-01-01 ERROR disk full
        2024-01-01 WARN  low memory
        2024-01-01 DEBUG checking health
    """)
    p = tmp_path / "app.log"
    p.write_text(content)
    return p


def _make_args(file, rules, tagged_only=False, summary=False):
    ns = argparse.Namespace(
        file=str(file),
        rules=rules,
        tagged_only=tagged_only,
        summary=summary,
        func=run_tagger,
    )
    return ns


def test_add_tagger_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_tagger_subparser(sub)
    args = parser.parse_args(["tag", "somefile.log", "-r", "E=error"])
    assert args.rules == ["E=error"]


def test_run_tagger_prints_tagged_lines(log_file, capsys):
    args = _make_args(log_file, ["ERR=error"])
    run_tagger(args)
    out = capsys.readouterr().out
    assert "[ERR]" in out
    assert "disk full" in out


def test_run_tagger_tagged_only_filters(log_file, capsys):
    args = _make_args(log_file, ["ERR=error"], tagged_only=True)
    run_tagger(args)
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert all("[ERR]" in ln for ln in lines)


def test_run_tagger_summary_printed(log_file, capsys):
    args = _make_args(log_file, ["ERR=error"], summary=True)
    run_tagger(args)
    out = capsys.readouterr().out
    assert "Tag Summary" in out
    assert "ERR" in out


def test_run_tagger_missing_file_exits(tmp_path, capsys):
    args = _make_args(tmp_path / "missing.log", ["E=error"])
    with pytest.raises(SystemExit) as exc_info:
        run_tagger(args)
    assert exc_info.value.code == 1


def test_run_tagger_no_rules_exits(log_file, capsys):
    args = _make_args(log_file, [])
    with pytest.raises(SystemExit) as exc_info:
        run_tagger(args)
    assert exc_info.value.code == 1


def test_run_tagger_bad_rule_exits(log_file, capsys):
    args = _make_args(log_file, ["NORULE"])
    with pytest.raises(SystemExit) as exc_info:
        run_tagger(args)
    assert exc_info.value.code == 1


def test_run_tagger_multiple_rules(log_file, capsys):
    args = _make_args(log_file, ["ERR=error", "WRN=warn"])
    run_tagger(args)
    out = capsys.readouterr().out
    assert "[ERR]" in out
    assert "[WRN]" in out
