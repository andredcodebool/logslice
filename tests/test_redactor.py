"""Tests for logslice.redactor."""

import pytest
from logslice.redactor import (
    build_patterns,
    redact_line,
    redact_lines,
    RedactResult,
    PLACEHOLDER,
)


# ---------------------------------------------------------------------------
# build_patterns
# ---------------------------------------------------------------------------

def test_build_patterns_empty():
    assert build_patterns() == []


def test_build_patterns_unknown_raises():
    with pytest.raises(ValueError, match="Unknown builtin"):
        build_patterns(builtins=["ssn"])


def test_build_patterns_builtin_email():
    patterns = build_patterns(builtins=["email"])
    assert len(patterns) == 1


def test_build_patterns_custom_compiles():
    patterns = build_patterns(custom=[r'secret=\S+'])
    assert len(patterns) == 1


# ---------------------------------------------------------------------------
# redact_line
# ---------------------------------------------------------------------------

def test_redact_line_email():
    patterns = build_patterns(builtins=["email"])
    result, subs = redact_line("user: alice@example.com logged in", patterns)
    assert "alice@example.com" not in result
    assert PLACEHOLDER in result
    assert subs == 1


def test_redact_line_ipv4():
    patterns = build_patterns(builtins=["ipv4"])
    result, subs = redact_line("request from 192.168.1.42", patterns)
    assert "192.168.1.42" not in result
    assert subs == 1


def test_redact_line_bearer():
    patterns = build_patterns(builtins=["bearer"])
    line = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
    result, subs = redact_line(line, patterns)
    assert "eyJhbGciOiJIUzI1NiJ9" not in result
    assert subs == 1


def test_redact_line_uuid():
    patterns = build_patterns(builtins=["uuid"])
    line = "session 123e4567-e89b-12d3-a456-426614174000 started"
    result, subs = redact_line(line, patterns)
    assert "123e4567" not in result
    assert subs == 1


def test_redact_line_no_match_returns_original():
    patterns = build_patterns(builtins=["email"])
    line = "nothing sensitive here"
    result, subs = redact_line(line, patterns)
    assert result == line
    assert subs == 0


def test_redact_line_custom_placeholder():
    patterns = build_patterns(builtins=["ipv4"])
    result, _ = redact_line("ip=10.0.0.1", patterns, placeholder="***")
    assert "***" in result
    assert "10.0.0.1" not in result


# ---------------------------------------------------------------------------
# redact_lines
# ---------------------------------------------------------------------------

def test_redact_lines_returns_redact_result():
    result = redact_lines(["hello world"], builtins=["email"])
    assert isinstance(result, RedactResult)


def test_redact_lines_counts():
    lines = [
        "user a@b.com",
        "no email here",
        "user c@d.org and e@f.io",
    ]
    result = redact_lines(lines, builtins=["email"])
    assert result.total == 3
    assert result.redacted_count == 2
    assert result.substitutions == 3


def test_redact_lines_output_length():
    lines = ["ip 1.2.3.4", "clean line", "ip 5.6.7.8"]
    result = redact_lines(lines, builtins=["ipv4"])
    assert len(result.lines) == 3


def test_redact_lines_multiple_builtins():
    lines = ["email a@b.com ip 1.2.3.4"]
    result = redact_lines(lines, builtins=["email", "ipv4"])
    assert result.substitutions == 2
    assert result.redacted_count == 1


def test_redact_lines_custom_pattern():
    lines = ["secret=abc123", "public info"]
    result = redact_lines(lines, custom=[r'secret=\S+'])
    assert PLACEHOLDER in result.lines[0]
    assert result.lines[1] == "public info"
