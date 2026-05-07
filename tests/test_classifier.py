"""Tests for logslice.classifier."""
import pytest
from logslice.classifier import classify_lines, ClassifyResult, _extract_level


# ---------------------------------------------------------------------------
# _extract_level
# ---------------------------------------------------------------------------

def test_extract_level_error():
    assert _extract_level("2024-01-01 ERROR something broke") == "ERROR"


def test_extract_level_warning_short():
    assert _extract_level("[WARN] disk space low") == "WARNING"


def test_extract_level_warning_long():
    assert _extract_level("[WARNING] disk space low") == "WARNING"


def test_extract_level_fatal_normalised():
    assert _extract_level("FATAL: process exited") == "CRITICAL"


def test_extract_level_none():
    assert _extract_level("no level here") is None


def test_extract_level_case_insensitive():
    assert _extract_level("info: server started") == "INFO"


# ---------------------------------------------------------------------------
# classify_lines — basic
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_lines():
    return [
        "2024-01-01 INFO  server started",
        "2024-01-01 DEBUG loading config",
        "2024-01-01 ERROR connection refused",
        "2024-01-01 WARNING high memory",
        "plain text with no level",
    ]


def test_classify_returns_result(sample_lines):
    result = classify_lines(sample_lines)
    assert isinstance(result, ClassifyResult)


def test_classify_total(sample_lines):
    result = classify_lines(sample_lines)
    assert result.total == 5


def test_classify_error_bucket(sample_lines):
    result = classify_lines(sample_lines)
    assert result.count("ERROR") == 1


def test_classify_info_bucket(sample_lines):
    result = classify_lines(sample_lines)
    assert result.count("INFO") == 1


def test_classify_unclassified(sample_lines):
    result = classify_lines(sample_lines)
    assert len(result.unclassified) == 1
    assert "plain text" in result.unclassified[0]


def test_classify_dominant_level():
    lines = [
        "ERROR one",
        "ERROR two",
        "INFO three",
    ]
    result = classify_lines(lines)
    assert result.dominant_level() == "ERROR"


def test_classify_dominant_level_none():
    result = classify_lines(["no levels here", "still nothing"])
    assert result.dominant_level() is None


# ---------------------------------------------------------------------------
# classify_lines — extra patterns
# ---------------------------------------------------------------------------

def test_extra_pattern_creates_bucket():
    lines = ["timeout waiting for response", "INFO all good"]
    result = classify_lines(lines, extra_patterns={"TIMEOUT": r"timeout"})
    assert result.count("TIMEOUT") == 1


def test_extra_pattern_takes_priority_over_builtin():
    lines = ["ERROR timeout occurred"]
    result = classify_lines(lines, extra_patterns={"TIMEOUT": r"timeout"})
    # extra pattern matched first
    assert result.count("TIMEOUT") == 1
    assert result.count("ERROR") == 0


def test_extra_pattern_label_uppercased():
    lines = ["retry attempt 3"]
    result = classify_lines(lines, extra_patterns={"retry": r"retry"})
    assert "RETRY" in result.buckets


def test_empty_lines_gives_empty_result():
    result = classify_lines([])
    assert result.total == 0
    assert result.buckets == {}
    assert result.unclassified == []
