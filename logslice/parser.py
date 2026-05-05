"""Log line parser: extracts timestamps and matches regex filters."""

import re
from datetime import datetime
from typing import Optional

# Common timestamp formats found in log files
TIMESTAMP_PATTERNS = [
    (r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)", "%Y-%m-%dT%H:%M:%S"),
    (r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", "%Y-%m-%d %H:%M:%S"),
    (r"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})", "%d/%b/%Y:%H:%M:%S"),
    (r"(\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2})", "%b %d %H:%M:%S"),
]


def extract_timestamp(line: str) -> Optional[datetime]:
    """Try each known pattern and return the first parsed datetime, or None."""
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if match:
            raw = match.group(1).replace("T", " ").rstrip("Z")
            # Trim sub-seconds and timezone offset for simple parsing
            raw = re.sub(r"\.\d+", "", raw)
            raw = re.sub(r"[+-]\d{2}:?\d{2}$", "", raw).strip()
            try:
                return datetime.strptime(raw, fmt.replace("T", " "))
            except ValueError:
                continue
    return None


def line_matches_filter(line: str, pattern: Optional[re.Pattern]) -> bool:
    """Return True if no filter is set, or if the compiled regex matches the line."""
    if pattern is None:
        return True
    return bool(pattern.search(line))


def compile_filter(regex: Optional[str]) -> Optional[re.Pattern]:
    """Compile a regex string into a pattern object, or return None."""
    if not regex:
        return None
    return re.compile(regex)
