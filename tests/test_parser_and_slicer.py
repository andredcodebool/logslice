"""Tests for logslice.parser and logslice.slicer."""

import re
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from logslice.parser import compile_filter, extract_timestamp, line_matches_filter
from logslice.slicer import slice_log


# ---------------------------------------------------------------------------
# parser tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line,expected", [
    ("2024-03-15T08:30:00Z INFO server started", datetime(2024, 3, 15, 8, 30, 0)),
    ("2024-03-15 08:30:00 ERROR disk full", datetime(2024, 3, 15, 8, 30, 0)),
    ("15/Mar/2024:08:30:00 GET /index.html", datetime(2024, 3, 15, 8, 30, 0)),
    ("no timestamp here at all", None),
])
def test_extract_timestamp(line, expected):
    assert extract_timestamp(line) == expected


def test_line_matches_filter_no_pattern():
    assert line_matches_filter("anything", None) is True


def test_line_matches_filter_with_pattern():
    pat = re.compile(r"ERROR")
    assert line_matches_filter("2024-01-01 ERROR boom", pat) is True
    assert line_matches_filter("2024-01-01 INFO ok", pat) is False


def test_compile_filter_none():
    assert compile_filter(None) is None
    assert compile_filter("") is None


def test_compile_filter_valid():
    pat = compile_filter(r"\d+")
    assert pat is not None
    assert pat.search("abc 123")


# ---------------------------------------------------------------------------
# slicer tests
# ---------------------------------------------------------------------------

LOG_CONTENT = textwrap.dedent("""\
    2024-03-15 08:00:00 INFO  boot sequence started
    2024-03-15 08:05:00 DEBUG config loaded
    2024-03-15 08:10:00 ERROR disk read failure
    2024-03-15 08:15:00 INFO  recovery attempted
    2024-03-15 08:20:00 INFO  all systems nominal
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(LOG_CONTENT)
    return p


def test_slice_all_lines(log_file):
    lines = list(slice_log(log_file))
    assert len(lines) == 5


def test_slice_with_start(log_file):
    start = datetime(2024, 3, 15, 8, 10, 0)
    lines = list(slice_log(log_file, start=start))
    assert all("08:10" in l or "08:15" in l or "08:20" in l for l in lines)
    assert len(lines) == 3


def test_slice_with_end(log_file):
    end = datetime(2024, 3, 15, 8, 5, 0)
    lines = list(slice_log(log_file, end=end))
    assert len(lines) == 2


def test_slice_with_regex(log_file):
    lines = list(slice_log(log_file, regex=r"ERROR|DEBUG"))
    assert len(lines) == 2


def test_slice_file_not_found():
    with pytest.raises(FileNotFoundError):
        list(slice_log("/nonexistent/path/app.log"))
