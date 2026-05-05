"""Output formatting utilities for logslice results."""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SliceResult:
    """Holds the result of a log slicing operation."""
    lines: List[str] = field(default_factory=list)
    matched_count: int = 0
    total_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def match_ratio(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.matched_count / self.total_count


def format_output(result: SliceResult, show_summary: bool = True) -> str:
    """Format a SliceResult into a printable string.

    Args:
        result: The SliceResult to format.
        show_summary: Whether to append a summary footer.

    Returns:
        Formatted string ready for output.
    """
    parts = list(result.lines)

    if show_summary:
        parts.append("")
        parts.append("--- logslice summary ---")
        parts.append(f"Matched lines : {result.matched_count}")
        parts.append(f"Total lines   : {result.total_count}")
        ratio_pct = f"{result.match_ratio * 100:.1f}%"
        parts.append(f"Match ratio   : {ratio_pct}")
        if result.start_time:
            parts.append(f"First match   : {result.start_time.isoformat()}")
        if result.end_time:
            parts.append(f"Last match    : {result.end_time.isoformat()}")

    return "\n".join(parts)


def format_jsonl(result: SliceResult) -> str:
    """Format matched lines as JSON-Lines (one JSON object per line).

    Args:
        result: The SliceResult to format.

    Returns:
        JSONL string where each line is a JSON object with a 'line' key.
    """
    import json
    return "\n".join(json.dumps({"line": ln}) for ln in result.lines)
