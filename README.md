# logslice

Fast log file slicer with time-range and regex filtering for local debugging.

## Features

- **slice** – Extract lines within a time range
- **filter** – Regex include/exclude filtering
- **highlight** – Colorise log levels and patterns
- **export** – Write results to `.txt`, `.jsonl`, or `.csv`
- **stats / report** – Counts, rates, and level breakdowns
- **watch** – Tail a live log file with optional filters
- **bookmark** – Save and restore file positions
- **context** – Show lines before/after a match (`-B`/`-A`)
- **dedup** – Remove duplicate log lines
- **sample** – Keep every-N, random, or head subset of lines
- **diff** – Compare two log files line-by-line
- **merge** – Interleave multiple log files in timestamp order
- **truncate** – Keep first/last/middle N lines
- **split** – Divide a log into chunks by lines, size, or time
- **redact** – Mask sensitive data (emails, IPs, UUIDs, …)
- **annotate** – Tag lines with custom labels
- **normalize** – Standardise timestamps and levels
- **summarize** – One-line digest of a log file
- **classify** – Dominant log-level classification
- **profile** – Line-rate histogram over time windows
- **score** – Assign severity scores to lines
- **tag** – Attach user-defined tags to matching lines
- **pipeline** – Chain grep / drop / replace stages
- **group** – Bucket lines by capture pattern or time window

## Installation

```bash
pip install logslice
```

## Quick start

```bash
# Slice by time range
logslice slice app.log --start "2024-01-01 08:00" --end "2024-01-01 09:00"

# Filter with regex
logslice slice app.log --filter ERROR

# Group by log level
logslice group app.log --pattern "(ERROR|WARN|INFO|DEBUG)"

# Group by 5-minute time windows
logslice group app.log --window 300

# Export to CSV
logslice slice app.log --filter ERROR --export out.csv

# Watch live with filter
logslice watch app.log --filter CRITICAL

# Deduplicate
logslice dedup app.log

# Show stats report
logslice stats app.log
```

## group sub-command

```
usage: logslice group [-h] (--pattern REGEX | --window SECONDS)
                      [--show-ungrouped] file

positional arguments:
  file               Log file to process

options:
  --pattern REGEX    Regex with one capture group used as the bucket key
  --window SECONDS   Group by fixed time window (seconds)
  --show-ungrouped   Also print lines that could not be grouped
```

## Development

```bash
pip install -e .[dev]
pytest
```
