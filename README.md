# logslice

Fast log file slicer with time-range and regex filtering for local debugging.

## Features

- **slice** — Extract lines within a time range
- **filter** — Regex-based line filtering
- **highlight** — Colorize log levels and patterns
- **export** — Save results as TXT, JSONL, or CSV
- **stats / report** — Summarize log level distributions
- **watch** — Tail a log file in real time
- **bookmark** — Save and restore positions in a log file
- **context** — Show lines surrounding a match
- **dedup** — Remove duplicate log lines
- **sample** — Randomly or periodically sample lines
- **diff** — Compare two log files
- **merge** — Merge multiple log files in chronological order
- **truncate** — Keep only the head, tail, or middle of a log
- **split** — Split a log by line count, size, or time window
- **redact** — Mask sensitive data (emails, IPs, UUIDs, custom patterns)
- **annotate** — Attach notes to matching lines
- **normalize** — Standardize timestamps, levels, and custom fields
- **summarize** — High-level summary of a log file
- **classify** — Determine the dominant log level of a file
- **profile** — Count events per time window
- **score** — Rank lines by severity and keyword weight
- **tag** — Label lines with user-defined regex-based tags

## Installation

```bash
pip install logslice
```

## Quick Start

```bash
# Slice by time range
logslice slice app.log --start "2024-01-01 08:00" --end "2024-01-01 09:00"

# Filter with regex
logslice slice app.log --filter "ERROR|WARN"

# Tag lines with labels
logslice tag app.log -r ERR=error -r WRN=warn --summary

# Tag and show only matching lines
logslice tag app.log -r CRITICAL=critical --tagged-only

# Export to CSV
logslice slice app.log --export out.csv

# Watch live
logslice watch app.log

# Deduplicate
logslice dedup app.log

# Score by severity
logslice score app.log --threshold 5
```

## Tag Rules

Rules follow the `LABEL=PATTERN` format where `PATTERN` is a Python regex.
Multiple rules can be applied; a line may receive more than one tag.

```bash
logslice tag app.log \
  -r ERROR=error \
  -r SLOW='took [0-9]+ms' \
  -r AUTH='(login|logout|auth)' \
  --tagged-only \
  --summary
```

## License

MIT
