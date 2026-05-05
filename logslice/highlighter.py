"""Terminal highlighting utilities for matched log lines."""

import re
from typing import Optional

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"

LEVEL_COLORS = {
    "ERROR": RED,
    "CRITICAL": RED + BOLD,
    "WARNING": YELLOW,
    "WARN": YELLOW,
    "INFO": GREEN,
    "DEBUG": CYAN,
}


def colorize_level(line: str) -> str:
    """Apply color to known log level keywords found in the line."""
    for level, color in LEVEL_COLORS.items():
        if level in line:
            line = line.replace(level, f"{color}{level}{RESET}", 1)
            break
    return line


def highlight_pattern(line: str, pattern: Optional[re.Pattern]) -> str:
    """Highlight all occurrences of a compiled regex pattern in the line."""
    if pattern is None:
        return line

    def replacer(match: re.Match) -> str:
        return f"{MAGENTA}{BOLD}{match.group(0)}{RESET}"

    return pattern.sub(replacer, line)


def highlight_line(
    line: str,
    pattern: Optional[re.Pattern] = None,
    colorize_levels: bool = True,
) -> str:
    """Apply all highlighting to a single log line.

    Args:
        line: Raw log line string.
        pattern: Optional compiled regex whose matches will be highlighted.
        colorize_levels: Whether to colorize log-level keywords.

    Returns:
        Line with ANSI escape codes applied.
    """
    if colorize_levels:
        line = colorize_level(line)
    line = highlight_pattern(line, pattern)
    return line


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from *text* (useful for plain-text output)."""
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)
