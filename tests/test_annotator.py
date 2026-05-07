"""Tests for logslice.annotator and logslice.cli_annotator."""
from __future__ import annotations

import argparse

import pytest

from logslice.annotator import (
    Annotation,
    AnnotateResult,
    annotate_lines,
    format_annotations,
)
from logslice.cli_annotator import add_annotator_subparser, run_annotator


SAMPLE_LINES = [
    "2024-01-01 INFO  service started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 WARN  memory low\n",
    "2024-01-01 DEBUG heartbeat\n",
    "2024-01-01 ERROR timeout reached\n",
]


def _rules():
    return [
        (r"ERROR", "error", "needs attention"),
        (r"WARN", "warning", None),
    ]


def test_annotate_lines_returns_result():
    result = annotate_lines(SAMPLE_LINES, _rules())
    assert isinstance(result, AnnotateResult)


def test_annotate_lines_total_lines():
    result = annotate_lines(SAMPLE_LINES, _rules())
    assert result.total_lines == len(SAMPLE_LINES)


def test_annotate_lines_correct_count():
    result = annotate_lines(SAMPLE_LINES, _rules())
    assert result.annotated_count == 3  # 2 ERRORs + 1 WARN


def test_annotate_lines_tags():
    result = annotate_lines(SAMPLE_LINES, _rules())
    tags = [a.tag for a in result.annotations]
    assert tags.count("error") == 2
    assert tags.count("warning") == 1


def test_annotate_lines_note_attached():
    result = annotate_lines(SAMPLE_LINES, _rules())
    error_anns = [a for a in result.annotations if a.tag == "error"]
    assert all(a.note == "needs attention" for a in error_anns)


def test_annotate_lines_no_rules_returns_empty():
    result = annotate_lines(SAMPLE_LINES, [])
    assert result.annotated_count == 0


def test_annotate_lines_first_rule_wins():
    # Both rules would match a hypothetical line — first tag should win.
    lines = ["ERROR WARN both\n"]
    result = annotate_lines(lines, _rules())
    assert result.annotations[0].tag == "error"


def test_annotation_str_with_note():
    ann = Annotation(line_number=2, original="ERROR disk full\n", tag="error", note="critical")
    text = str(ann)
    assert "[error]" in text
    assert "L2" in text
    assert "critical" in text


def test_annotation_str_without_note():
    ann = Annotation(line_number=3, original="WARN low\n", tag="warning")
    text = str(ann)
    assert "—" not in text


def test_format_annotations_summary_present():
    result = annotate_lines(SAMPLE_LINES, _rules())
    output = format_annotations(result)
    assert "annotation" in output


def test_format_annotations_no_summary():
    result = annotate_lines(SAMPLE_LINES, _rules())
    output = format_annotations(result, show_summary=False)
    assert "annotation" not in output


def test_cli_run_annotator_prints_output(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text("".join(SAMPLE_LINES))
    ns = argparse.Namespace(
        logfile=str(log),
        rules=[("ERROR", "error")],
        notes=["watch out"],
        no_summary=False,
        func=run_annotator,
    )
    run_annotator(ns)
    captured = capsys.readouterr()
    assert "error" in captured.out


def test_cli_run_annotator_missing_file_exits(tmp_path):
    ns = argparse.Namespace(
        logfile=str(tmp_path / "missing.log"),
        rules=[("ERROR", "error")],
        notes=[],
        no_summary=False,
        func=run_annotator,
    )
    with pytest.raises(SystemExit):
        run_annotator(ns)


def test_add_annotator_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_annotator_subparser(sub)
    args = parser.parse_args(["annotate", "some.log", "--rule", "ERROR", "err"])
    assert args.rules == [["ERROR", "err"]]
