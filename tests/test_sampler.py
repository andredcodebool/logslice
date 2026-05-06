"""Tests for logslice.sampler and logslice.cli_sampler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

from logslice.sampler import SampleResult, sample_every_n, sample_head, sample_random
from logslice.cli_sampler import add_sampler_subparser, run_sampler


LINES = [f"line {i}\n" for i in range(1, 11)]  # 10 lines


# ---------------------------------------------------------------------------
# sample_every_n
# ---------------------------------------------------------------------------

def test_every_n_basic():
    result = sample_every_n(LINES, 2)
    assert result.total_input == 10
    assert result.total_output == 5
    assert result.lines == [LINES[1], LINES[3], LINES[5], LINES[7], LINES[9]]


def test_every_n_one_keeps_all():
    result = sample_every_n(LINES, 1)
    assert result.total_output == 10
    assert result.lines == LINES


def test_every_n_invalid_raises():
    with pytest.raises(ValueError, match="n must be >= 1"):
        sample_every_n(LINES, 0)


def test_every_n_ratio():
    result = sample_every_n(LINES, 5)
    assert result.ratio == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# sample_random
# ---------------------------------------------------------------------------

def test_sample_random_fraction_one_keeps_all():
    result = sample_random(LINES, 1.0, seed=42)
    assert result.total_output == 10


def test_sample_random_reproducible():
    r1 = sample_random(LINES, 0.5, seed=7)
    r2 = sample_random(LINES, 0.5, seed=7)
    assert r1.lines == r2.lines


def test_sample_random_invalid_fraction():
    with pytest.raises(ValueError, match="fraction must be in"):
        sample_random(LINES, 0.0)

    with pytest.raises(ValueError, match="fraction must be in"):
        sample_random(LINES, 1.5)


def test_sample_random_empty_input():
    result = sample_random([], 0.5, seed=0)
    assert result.total_input == 0
    assert result.ratio == 0.0


# ---------------------------------------------------------------------------
# sample_head
# ---------------------------------------------------------------------------

def test_head_fewer_than_available():
    result = sample_head(LINES, 3)
    assert result.total_output == 3
    assert result.lines == LINES[:3]


def test_head_more_than_available():
    result = sample_head(LINES, 100)
    assert result.total_output == 10


def test_head_zero():
    result = sample_head(LINES, 0)
    assert result.total_output == 0
    assert result.lines == []


def test_head_negative_raises():
    with pytest.raises(ValueError, match="count must be >= 0"):
        sample_head(LINES, -1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text("".join(LINES), encoding="utf-8")
    return p


def _make_args(log_file: Path, **kwargs):
    ns = argparse.Namespace(
        file=str(log_file),
        every=None,
        fraction=None,
        head=None,
        seed=None,
        output=None,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_run_sampler_every(log_file: Path, capsys):
    args = _make_args(log_file, every=2)
    run_sampler(args)
    captured = capsys.readouterr()
    assert "line 2" in captured.out
    assert "line 1\n" not in captured.out


def test_run_sampler_head_to_file(log_file: Path, tmp_path: Path):
    out = tmp_path / "out.log"
    args = _make_args(log_file, head=3, output=str(out))
    run_sampler(args)
    content = out.read_text(encoding="utf-8")
    assert content.count("line") == 3


def test_run_sampler_missing_file(tmp_path: Path):
    args = _make_args(tmp_path / "no.log", every=1)
    with pytest.raises(SystemExit):
        run_sampler(args)


def test_add_sampler_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_sampler_subparser(sub)
    ns = parser.parse_args(["sample", "some.log", "--head", "5"])
    assert ns.head == 5
