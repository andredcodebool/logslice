"""Tests for logslice/pipeline.py"""
import pytest
from logslice.pipeline import Pipeline, PipelineResult, Stage, build_pipeline


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _keep_all(line: str):
    return line


def _drop_all(line: str):
    return None


def _upper(line: str):
    return line.upper()


LINES = ["INFO hello", "ERROR world", "DEBUG foo", "WARNING bar"]


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

def test_stage_apply_returns_transformed():
    s = Stage(name="upper", transform=_upper)
    assert s.apply("hello") == "HELLO"


def test_stage_apply_returns_none_when_dropped():
    s = Stage(name="drop", transform=_drop_all)
    assert s.apply("anything") is None


# ---------------------------------------------------------------------------
# Pipeline.run — basic
# ---------------------------------------------------------------------------

def test_empty_pipeline_passes_all_lines():
    p = Pipeline()
    result = p.run(LINES)
    assert result.output == LINES
    assert result.lines_in == 4
    assert result.lines_out == 4
    assert result.dropped == 0


def test_pipeline_drop_all_produces_empty_output():
    p = Pipeline([Stage("drop", _drop_all)])
    result = p.run(LINES)
    assert result.output == []
    assert result.lines_out == 0
    assert result.dropped == 4


def test_pipeline_transform_applied():
    p = Pipeline([Stage("upper", _upper)])
    result = p.run(["hello", "world"])
    assert result.output == ["HELLO", "WORLD"]


def test_pipeline_filter_stage():
    import re
    rx = re.compile(r"ERROR")
    stage = Stage("grep-error", lambda l: l if rx.search(l) else None)
    p = Pipeline([stage])
    result = p.run(LINES)
    assert result.output == ["ERROR world"]
    assert result.lines_out == 1
    assert result.dropped == 3


# ---------------------------------------------------------------------------
# Pipeline chaining
# ---------------------------------------------------------------------------

def test_pipeline_chained_stages():
    import re
    keep_error = Stage("grep", lambda l: l if re.search(r"ERROR|WARNING", l) else None)
    upper = Stage("upper", _upper)
    p = Pipeline([keep_error, upper])
    result = p.run(LINES)
    assert result.output == ["ERROR WORLD", "WARNING BAR"]


def test_add_stage_returns_pipeline():
    p = Pipeline()
    returned = p.add_stage(Stage("noop", _keep_all))
    assert returned is p
    assert len(p.stages) == 1


def test_stage_names_in_result():
    p = Pipeline([
        Stage("first", _keep_all),
        Stage("second", _upper),
    ])
    result = p.run(["a"])
    assert result.stage_names == ["first", "second"]


# ---------------------------------------------------------------------------
# PipelineResult helpers
# ---------------------------------------------------------------------------

def test_retention_rate_full():
    p = Pipeline()
    result = p.run(["a", "b", "c"])
    assert result.retention_rate == pytest.approx(1.0)


def test_retention_rate_zero_total():
    p = Pipeline()
    result = p.run([])
    assert result.retention_rate == 0.0


def test_retention_rate_partial():
    import re
    rx = re.compile(r"keep")
    p = Pipeline([Stage("filter", lambda l: l if rx.search(l) else None)])
    result = p.run(["keep this", "drop this", "keep me too"])
    assert result.retention_rate == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

def test_build_pipeline_returns_pipeline_instance():
    stages = [Stage("noop", _keep_all)]
    p = build_pipeline(stages)
    assert isinstance(p, Pipeline)
    assert p.stages == stages


def test_build_pipeline_empty_stages():
    p = build_pipeline([])
    result = p.run(["hello"])
    assert result.output == ["hello"]
