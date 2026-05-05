"""Tests for logslice.highlighter."""

import re
import pytest

from logslice.highlighter import (
    colorize_level,
    highlight_pattern,
    highlight_line,
    strip_ansi,
    RESET,
    RED,
    YELLOW,
    GREEN,
    CYAN,
    MAGENTA,
    BOLD,
)


def test_colorize_level_error():
    line = "2024-01-01 12:00:00 ERROR something went wrong"
    result = colorize_level(line)
    assert "ERROR" in result
    assert RED in result
    assert RESET in result


def test_colorize_level_warning():
    line = "2024-01-01 12:00:00 WARNING disk space low"
    result = colorize_level(line)
    assert YELLOW in result


def test_colorize_level_info():
    line = "2024-01-01 12:00:00 INFO service started"
    result = colorize_level(line)
    assert GREEN in result


def test_colorize_level_debug():
    line = "2024-01-01 12:00:00 DEBUG entering function"
    result = colorize_level(line)
    assert CYAN in result


def test_colorize_level_no_known_level():
    line = "2024-01-01 12:00:00 just a plain line"
    result = colorize_level(line)
    # No color codes should be added
    assert result == line


def test_highlight_pattern_none():
    line = "some log line with keyword"
    result = highlight_pattern(line, None)
    assert result == line


def test_highlight_pattern_marks_match():
    pattern = re.compile(r"keyword")
    line = "some log line with keyword inside"
    result = highlight_pattern(line, pattern)
    assert MAGENTA in result
    assert BOLD in result
    assert RESET in result
    assert "keyword" in result


def test_highlight_pattern_multiple_matches():
    pattern = re.compile(r"foo")
    line = "foo bar foo baz foo"
    result = highlight_pattern(line, pattern)
    assert result.count(MAGENTA) == 3


def test_highlight_line_combines_both():
    pattern = re.compile(r"timeout")
    line = "2024-01-01 ERROR connection timeout occurred"
    result = highlight_line(line, pattern=pattern, colorize_levels=True)
    assert RED in result          # level color
    assert MAGENTA in result      # pattern highlight


def test_highlight_line_no_colorize_levels():
    line = "2024-01-01 ERROR something"
    result = highlight_line(line, pattern=None, colorize_levels=False)
    assert RED not in result


def test_strip_ansi_removes_codes():
    colored = f"{RED}hello{RESET} {BOLD}world{RESET}"
    plain = strip_ansi(colored)
    assert plain == "hello world"


def test_strip_ansi_plain_string():
    plain = "no colors here"
    assert strip_ansi(plain) == plain
