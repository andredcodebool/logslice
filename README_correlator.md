# logslice correlate

Correlate log lines across **multiple files** by a shared token such as a
request-id, trace-id, or session-id.

## Quick start

```bash
# Basic usage – group lines by request-id
logslice correlate app.log db.log --pattern 'req=(?P<token>[\w-]+)'

# Custom labels for each file
logslice correlate frontend=app.log backend=db.log \
    --pattern 'req_id=(?P<token>[\w-]+)'

# Show lines that contained no token
logslice correlate app.log db.log \
    --pattern 'req=(?P<token>[\w-]+)' \
    --show-unmatched

# Summary only
logslice correlate app.log db.log \
    --pattern 'req=(?P<token>[\w-]+)' \
    --summary
```

## Pattern rules

The `--pattern` regex **must** contain a named capture group called `token`:

```
(?P<token>...)
```

Examples:

| Use-case | Pattern |
|---|---|
| Request-id | `req_id=(?P<token>[\w-]+)` |
| UUID anywhere | `(?P<token>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})` |
| Session cookie | `session=(?P<token>[A-Za-z0-9]+)` |

## Output

```
[token=abc123]  (3 lines)
  app.log: 2024-01-15 10:00:01 req_id=abc123 INFO  GET /api/users
  db.log:  2024-01-15 10:00:01 req_id=abc123 DEBUG SELECT * FROM users
  app.log: 2024-01-15 10:00:02 req_id=abc123 INFO  200 OK

-- 1 group(s), 3 line(s) total --
```

## Python API

```python
from logslice.correlator import correlate, format_correlation

result = correlate(
    sources=[
        ("app",  open("app.log")),
        ("db",   open("db.log")),
    ],
    pattern=r"req=(?P<token>[\w-]+)",
)
print(format_correlation(result, show_unmatched=True))
```
