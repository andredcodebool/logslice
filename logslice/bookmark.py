"""Bookmark support: save and restore log-reading positions by file path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

DEFAULT_BOOKMARK_FILE = Path.home() / ".logslice_bookmarks.json"


def _load(bookmark_file: Path) -> Dict[str, int]:
    """Load bookmark data from disk, returning empty dict on missing/corrupt file."""
    if not bookmark_file.exists():
        return {}
    try:
        with bookmark_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save(data: Dict[str, int], bookmark_file: Path) -> None:
    """Persist bookmark data to disk."""
    bookmark_file.parent.mkdir(parents=True, exist_ok=True)
    with bookmark_file.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def save_bookmark(
    log_path: str,
    byte_offset: int,
    bookmark_file: Path = DEFAULT_BOOKMARK_FILE,
) -> None:
    """Record *byte_offset* as the last-read position for *log_path*."""
    key = str(Path(log_path).resolve())
    data = _load(bookmark_file)
    data[key] = byte_offset
    _save(data, bookmark_file)


def load_bookmark(
    log_path: str,
    bookmark_file: Path = DEFAULT_BOOKMARK_FILE,
) -> Optional[int]:
    """Return the saved byte offset for *log_path*, or None if not bookmarked."""
    key = str(Path(log_path).resolve())
    data = _load(bookmark_file)
    return data.get(key)


def clear_bookmark(
    log_path: str,
    bookmark_file: Path = DEFAULT_BOOKMARK_FILE,
) -> bool:
    """Remove the bookmark for *log_path*. Returns True if a bookmark existed."""
    key = str(Path(log_path).resolve())
    data = _load(bookmark_file)
    if key in data:
        del data[key]
        _save(data, bookmark_file)
        return True
    return False


def list_bookmarks(
    bookmark_file: Path = DEFAULT_BOOKMARK_FILE,
) -> Dict[str, int]:
    """Return all saved bookmarks as {resolved_path: byte_offset}."""
    return dict(_load(bookmark_file))
