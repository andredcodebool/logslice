"""Human-readable and JSON report generation from LogStats."""
from __future__ import annotations

import json
from typing import Optional

from logslice.stats import LogStats


BAR_WIDTH = 20


def _level_bar(count: int, total: int) -> str:
    """Return a simple ASCII bar proportional to count/total."""
    if total == 0:
        return ""
    filled = round(BAR_WIDTH * count / total)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + "]"


def format_stats_text(stats: LogStats, title: str = "Log Statistics") -> str:
    """Render LogStats as a human-readable text block."""
    lines = [
        f"=== {title} ===",
        f"  Total lines scanned : {stats.total_lines}",
        f"  Matched lines       : {stats.matched_lines}",
    ]

    if stats.first_timestamp:
        lines.append(f"  First timestamp     : {stats.first_timestamp}")
    if stats.last_timestamp:
        lines.append(f"  Last timestamp      : {stats.last_timestamp}")

    if stats.level_counts:
        lines.append("  Level breakdown:")
        total_leveled = sum(stats.level_counts.values())
        for level, count in sorted(stats.level_counts.items()):
            bar = _level_bar(count, total_leveled)
            lines.append(f"    {level:<10} {bar} {count}")

    lines.append(f"  Errors / Warnings   : {stats.error_count} / {stats.warning_count}")
    lines.append("=" * (len(title) + 8))
    return "\n".join(lines)


def format_stats_json(stats: LogStats, indent: int = 2) -> str:
    """Render LogStats as a JSON string."""
    return json.dumps(stats.as_dict(), indent=indent)


def print_report(
    stats: LogStats,
    fmt: str = "text",
    title: str = "Log Statistics",
) -> None:
    """Print a stats report to stdout in the requested format."""
    if fmt == "json":
        print(format_stats_json(stats))
    else:
        print(format_stats_text(stats, title=title))
