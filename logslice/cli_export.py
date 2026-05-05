"""CLI helpers for the --export flag added to the logslice command."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from logslice.exporter import export_result
from logslice.formatter import SliceResult

_SUPPORTED_FORMATS = ("txt", "jsonl", "csv")


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """Attach export-related arguments to an existing ArgumentParser."""
    group = parser.add_argument_group("export")
    group.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Export matched lines to FILE.",
    )
    group.add_argument(
        "--export-format",
        choices=_SUPPORTED_FORMATS,
        default="txt",
        metavar="FMT",
        help=f"Export format: {', '.join(_SUPPORTED_FORMATS)} (default: txt).",
    )


def maybe_export(
    result: SliceResult,
    export_path: Optional[str],
    export_format: str = "txt",
) -> None:
    """Export *result* to *export_path* when a path is provided.

    Args:
        result:        The SliceResult produced by the slicer.
        export_path:   Destination file path string, or *None* to skip.
        export_format: Format string understood by :func:`export_result`.
    """
    if not export_path:
        return

    dest = Path(export_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    export_result(result, dest, fmt=export_format)
    print(f"[logslice] Exported {len(result.matched_lines)} line(s) to {dest} ({export_format})")
