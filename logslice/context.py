"""Context lines support: capture N lines before/after each matching line."""

from typing import List, Tuple, Optional
from collections import deque


def extract_with_context(
    lines: List[str],
    match_indices: List[int],
    before: int = 0,
    after: int = 0,
) -> List[Tuple[int, str, bool]]:
    """
    Given a list of lines and indices of matched lines, return a deduplicated
    list of (line_index, line_text, is_match) tuples respecting context windows.

    Args:
        lines:         All log lines.
        match_indices: Indices (into `lines`) that matched the filter.
        before:        Number of lines to include before each match.
        after:         Number of lines to include after each match.

    Returns:
        Sorted, deduplicated list of (index, text, is_match) tuples.
    """
    if not match_indices:
        return []

    included: dict[int, bool] = {}  # index -> is_match

    for idx in match_indices:
        # context before
        for offset in range(before, 0, -1):
            ctx_idx = idx - offset
            if 0 <= ctx_idx < len(lines) and ctx_idx not in included:
                included[ctx_idx] = False
        # the match itself
        included[idx] = True
        # context after
        for offset in range(1, after + 1):
            ctx_idx = idx + offset
            if 0 <= ctx_idx < len(lines) and ctx_idx not in included:
                included[ctx_idx] = False

    return [
        (i, lines[i], included[i])
        for i in sorted(included)
    ]


def format_context_block(
    context_entries: List[Tuple[int, str, bool]],
    separator: str = "--",
) -> List[str]:
    """
    Convert context entries into printable lines, inserting a separator between
    non-contiguous groups.

    Args:
        context_entries: Output of extract_with_context.
        separator:       String inserted between discontinuous groups.

    Returns:
        List of strings ready for display.
    """
    output: List[str] = []
    prev_idx: Optional[int] = None

    for idx, text, _ in context_entries:
        if prev_idx is not None and idx > prev_idx + 1:
            output.append(separator)
        output.append(text.rstrip("\n"))
        prev_idx = idx

    return output
