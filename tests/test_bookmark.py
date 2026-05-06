"""Tests for logslice.bookmark and logslice.cli_bookmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logslice.bookmark import (
    clear_bookmark,
    list_bookmarks,
    load_bookmark,
    save_bookmark,
)
from logslice.cli_bookmark import add_bookmark_subparser, run_bookmark


# ---------------------------------------------------------------------------
# bookmark module tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def bm_file(tmp_path: Path) -> Path:
    return tmp_path / "bookmarks.json"


def test_save_and_load(bm_file: Path) -> None:
    save_bookmark("/var/log/app.log", 1024, bookmark_file=bm_file)
    result = load_bookmark("/var/log/app.log", bookmark_file=bm_file)
    assert result == 1024


def test_load_missing_returns_none(bm_file: Path) -> None:
    assert load_bookmark("/no/such/file.log", bookmark_file=bm_file) is None


def test_overwrite_bookmark(bm_file: Path) -> None:
    save_bookmark("/var/log/app.log", 100, bookmark_file=bm_file)
    save_bookmark("/var/log/app.log", 200, bookmark_file=bm_file)
    assert load_bookmark("/var/log/app.log", bookmark_file=bm_file) == 200


def test_clear_existing(bm_file: Path) -> None:
    save_bookmark("/var/log/app.log", 512, bookmark_file=bm_file)
    removed = clear_bookmark("/var/log/app.log", bookmark_file=bm_file)
    assert removed is True
    assert load_bookmark("/var/log/app.log", bookmark_file=bm_file) is None


def test_clear_nonexistent(bm_file: Path) -> None:
    removed = clear_bookmark("/ghost.log", bookmark_file=bm_file)
    assert removed is False


def test_list_bookmarks_empty(bm_file: Path) -> None:
    assert list_bookmarks(bookmark_file=bm_file) == {}


def test_list_bookmarks_multiple(bm_file: Path, tmp_path: Path) -> None:
    f1 = str(tmp_path / "a.log")
    f2 = str(tmp_path / "b.log")
    save_bookmark(f1, 10, bookmark_file=bm_file)
    save_bookmark(f2, 20, bookmark_file=bm_file)
    bms = list_bookmarks(bookmark_file=bm_file)
    assert len(bms) == 2


def test_corrupt_bookmark_file_returns_empty(bm_file: Path) -> None:
    bm_file.write_text("not json", encoding="utf-8")
    assert list_bookmarks(bookmark_file=bm_file) == {}


# ---------------------------------------------------------------------------
# cli_bookmark tests
# ---------------------------------------------------------------------------


def _make_args(bm_file: Path, **kwargs) -> argparse.Namespace:  # type: ignore[type-arg]
    defaults = {"bm_file": str(bm_file)}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_bookmark_save(bm_file: Path, tmp_path: Path) -> None:
    log = str(tmp_path / "x.log")
    args = _make_args(bm_file, bm_action="save", log=log, offset=999)
    code = run_bookmark(args)
    assert code == 0
    assert load_bookmark(log, bookmark_file=bm_file) == 999


def test_run_bookmark_load_found(bm_file: Path, tmp_path: Path, capsys) -> None:
    log = str(tmp_path / "x.log")
    save_bookmark(log, 42, bookmark_file=bm_file)
    args = _make_args(bm_file, bm_action="load", log=log)
    code = run_bookmark(args)
    assert code == 0
    assert "42" in capsys.readouterr().out


def test_run_bookmark_load_missing(bm_file: Path, capsys) -> None:
    args = _make_args(bm_file, bm_action="load", log="/no/file.log")
    code = run_bookmark(args)
    assert code == 1


def test_run_bookmark_clear(bm_file: Path, tmp_path: Path) -> None:
    log = str(tmp_path / "x.log")
    save_bookmark(log, 7, bookmark_file=bm_file)
    args = _make_args(bm_file, bm_action="clear", log=log)
    code = run_bookmark(args)
    assert code == 0
    assert load_bookmark(log, bookmark_file=bm_file) is None


def test_run_bookmark_list(bm_file: Path, tmp_path: Path, capsys) -> None:
    log = str(tmp_path / "y.log")
    save_bookmark(log, 55, bookmark_file=bm_file)
    args = _make_args(bm_file, bm_action="list")
    code = run_bookmark(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "55" in out
