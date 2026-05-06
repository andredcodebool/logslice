"""Tests for logslice.watcher — tail_file generator and watch filter logic."""

import time
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from logslice.watcher import tail_file, watch, _parse_optional_dt


# ---------------------------------------------------------------------------
# _parse_optional_dt
# ---------------------------------------------------------------------------

def test_parse_optional_dt_none():
    assert _parse_optional_dt(None) is None


def test_parse_optional_dt_valid():
    from datetime import datetime
    result = _parse_optional_dt("2024-01-15T10:00:00")
    assert result == datetime(2024, 1, 15, 10, 0, 0)


def test_parse_optional_dt_invalid():
    with pytest.raises(ValueError):
        _parse_optional_dt("not-a-date")


# ---------------------------------------------------------------------------
# tail_file
# ---------------------------------------------------------------------------

def test_tail_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list_gen = tail_file(str(tmp_path / "nonexistent.log"))
        next(list_gen)


def test_tail_file_yields_appended_lines(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("")  # create empty file

    results = []
    stop = threading.Event()

    def reader():
        gen = tail_file(str(log), poll_interval=0.05)
        for line in gen:
            results.append(line)
            if len(results) >= 2:
                break

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    time.sleep(0.1)
    with open(log, "a") as fh:
        fh.write("line one\n")
        fh.write("line two\n")

    t.join(timeout=2.0)
    assert results == ["line one", "line two"]


# ---------------------------------------------------------------------------
# watch — output filtering
# ---------------------------------------------------------------------------

def test_watch_filters_by_pattern(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text("")

    lines_to_emit = [
        "2024-01-15T10:00:00 INFO  request started",
        "2024-01-15T10:00:01 ERROR something failed",
        "2024-01-15T10:00:02 INFO  request ended",
    ]

    with patch("logslice.watcher.tail_file", return_value=iter(lines_to_emit)):
        watch(str(log), pattern="ERROR", colorize=False)

    captured = capsys.readouterr()
    assert "something failed" in captured.out
    assert "request started" not in captured.out


def test_watch_filters_by_time_range(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text("")

    lines_to_emit = [
        "2024-01-15T09:00:00 INFO  too early",
        "2024-01-15T10:30:00 INFO  in range",
        "2024-01-15T12:00:00 INFO  too late",
    ]

    with patch("logslice.watcher.tail_file", return_value=iter(lines_to_emit)):
        watch(
            str(log),
            start="2024-01-15T10:00:00",
            end="2024-01-15T11:00:00",
            colorize=False,
        )

    captured = capsys.readouterr()
    assert "in range" in captured.out
    assert "too early" not in captured.out
    assert "too late" not in captured.out
