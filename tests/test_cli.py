"""Tests for logslice.cli."""

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from logslice.cli import build_parser, run


SAMPLE_LOG = textwrap.dedent("""\
    2024-01-01T09:00:00 INFO  startup complete
    2024-01-01T09:05:00 DEBUG polling
    2024-01-01T09:10:00 ERROR disk full
    2024-01-01T09:15:00 INFO  shutdown
""").strip()


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(SAMPLE_LOG)
    return str(p)


def test_build_parser_defaults():
    p = build_parser()
    args = p.parse_args(["myfile.log"])
    assert args.logfile == "myfile.log"
    assert args.start is None
    assert args.end is None
    assert args.pattern is None
    assert not args.no_summary
    assert not args.jsonl


def test_run_basic(log_file, capsys):
    exit_code = run([log_file, "--no-summary"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "startup complete" in captured.out
    assert "disk full" in captured.out


def test_run_with_filter(log_file, capsys):
    exit_code = run([log_file, "--filter", "ERROR", "--no-summary"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "disk full" in captured.out
    assert "startup complete" not in captured.out


def test_run_with_time_range(log_file, capsys):
    exit_code = run([
        log_file,
        "--start", "2024-01-01T09:04:00",
        "--end",   "2024-01-01T09:11:00",
        "--no-summary",
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "polling" in captured.out
    assert "disk full" in captured.out
    assert "startup complete" not in captured.out


def test_run_summary_present(log_file, capsys):
    run([log_file])
    captured = capsys.readouterr()
    assert "logslice summary" in captured.out
    assert "Total lines" in captured.out


def test_run_jsonl_output(log_file, capsys):
    import json
    exit_code = run([log_file, "--jsonl", "--filter", "INFO"])
    assert exit_code == 0
    captured = capsys.readouterr()
    for line in captured.out.strip().splitlines():
        obj = json.loads(line)
        assert "line" in obj


def test_run_missing_file(capsys):
    exit_code = run(["nonexistent_file.log"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "file not found" in captured.err


def test_invalid_datetime_arg(log_file):
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args([log_file, "--start", "not-a-date"])
