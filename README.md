# logslice

Fast log file slicer with time-range and regex filtering for local debugging.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Slice logs between two timestamps
logslice app.log --start "2024-03-01 08:00:00" --end "2024-03-01 09:00:00"

# Filter by regex pattern
logslice app.log --pattern "ERROR|CRITICAL"

# Combine time range and regex filter
logslice app.log --start "2024-03-01 08:00:00" --end "2024-03-01 09:00:00" --pattern "timeout"

# Write output to a file
logslice app.log --start "2024-03-01 08:00:00" --pattern "ERROR" --output errors.log
```

### Python API

```python
from logslice import slice_log

results = slice_log(
    filepath="app.log",
    start="2024-03-01 08:00:00",
    end="2024-03-01 09:00:00",
    pattern="ERROR"
)

for line in results:
    print(line)
```

---

## Features

- ⚡ Fast binary-search-based timestamp seeking
- 🔍 Regex filtering with full Python `re` support
- 📁 Supports plain text and gzip-compressed log files
- 🖥️ Simple CLI and importable Python API

---

## License

MIT © 2024 youruser