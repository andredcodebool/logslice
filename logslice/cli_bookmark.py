"""CLI helpers for bookmark sub-commands (save, load, clear, list)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from logslice.bookmark import (
    DEFAULT_BOOKMARK_FILE,
    clear_bookmark,
    list_bookmarks,
    load_bookmark,
    save_bookmark,
)


def add_bookmark_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'bookmark' sub-command group onto *subparsers*."""
    bm = subparsers.add_parser("bookmark", help="Manage log-file read bookmarks")
    bm_sub = bm.add_subparsers(dest="bm_action", required=True)

    # save
    sv = bm_sub.add_parser("save", help="Save a byte-offset bookmark for a log file")
    sv.add_argument("log", help="Path to the log file")
    sv.add_argument("offset", type=int, help="Byte offset to bookmark")
    sv.add_argument("--file", dest="bm_file", default=None, help="Bookmark store path")

    # load
    ld = bm_sub.add_parser("load", help="Print the saved bookmark offset for a log file")
    ld.add_argument("log", help="Path to the log file")
    ld.add_argument("--file", dest="bm_file", default=None, help="Bookmark store path")

    # clear
    cl = bm_sub.add_parser("clear", help="Remove the bookmark for a log file")
    cl.add_argument("log", help="Path to the log file")
    cl.add_argument("--file", dest="bm_file", default=None, help="Bookmark store path")

    # list
    ls = bm_sub.add_parser("list", help="List all saved bookmarks")
    ls.add_argument("--file", dest="bm_file", default=None, help="Bookmark store path")


def _bm_file(args: argparse.Namespace) -> Path:
    return Path(args.bm_file) if args.bm_file else DEFAULT_BOOKMARK_FILE


def run_bookmark(args: argparse.Namespace) -> int:
    """Dispatch bookmark sub-command; returns exit code."""
    action = args.bm_action
    bf = _bm_file(args)

    if action == "save":
        save_bookmark(args.log, args.offset, bookmark_file=bf)
        print(f"Bookmark saved: {args.log} @ offset {args.offset}")

    elif action == "load":
        offset = load_bookmark(args.log, bookmark_file=bf)
        if offset is None:
            print(f"No bookmark found for {args.log}")
            return 1
        print(offset)

    elif action == "clear":
        removed = clear_bookmark(args.log, bookmark_file=bf)
        if removed:
            print(f"Bookmark cleared for {args.log}")
        else:
            print(f"No bookmark found for {args.log}")
            return 1

    elif action == "list":
        bookmarks = list_bookmarks(bookmark_file=bf)
        if not bookmarks:
            print("No bookmarks saved.")
        else:
            for path, offset in bookmarks.items():
                print(f"{path}  {offset}")

    return 0
