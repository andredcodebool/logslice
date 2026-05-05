"""Export sliced log results to various file formats."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from logslice.formatter import SliceResult


def export_txt(result: SliceResult, dest: Union[str, Path]) -> None:
    """Write matched lines as plain text, one line per entry."""
    dest = Path(dest)
    dest.write_text("\n".join(result.matched_lines) + "\n", encoding="utf-8")


def export_jsonl(result: SliceResult, dest: Union[str, Path]) -> None:
    """Write matched lines as JSON-Lines, each line is a JSON object."""
    dest = Path(dest)
    with dest.open("w", encoding="utf-8") as fh:
        for line in result.matched_lines:
            fh.write(json.dumps({"line": line}) + "\n")


def export_csv(result: SliceResult, dest: Union[str, Path]) -> None:
    """Write matched lines as CSV with a single 'line' column."""
    dest = Path(dest)
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["line"])
        for line in result.matched_lines:
            writer.writerow([line])


def export_result(
    result: SliceResult,
    dest: Union[str, Path],
    fmt: str = "txt",
) -> None:
    """Dispatch export to the correct format handler.

    Args:
        result: The SliceResult to export.
        dest:   Destination file path.
        fmt:    One of 'txt', 'jsonl', 'csv'.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    handlers = {
        "txt": export_txt,
        "jsonl": export_jsonl,
        "csv": export_csv,
    }
    if fmt not in handlers:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose from {list(handlers)}.")
    handlers[fmt](result, dest)
