# logslice alert

The `alert` sub-command scans a log file against one or more **alert rules** and
reports every line that triggers a rule.

## Quick start

```bash
logslice alert app.log \
  --rule "OOM=out of memory" \
  --rule "DISK=disk full:ERROR"
```

## Rule syntax

```
LABEL=PATTERN
LABEL=PATTERN:LEVEL
```

| Part | Description |
|------|-------------|
| `LABEL` | Short name shown in output, e.g. `OOM` |
| `PATTERN` | Python regex matched against each line |
| `LEVEL` | Optional log-level guard (`ERROR`, `WARN`, `INFO`, `DEBUG`, `FATAL`) |

When a `LEVEL` is specified the pattern must **also** appear in a line that
contains that level string (case-insensitive).

## Options

| Flag | Description |
|------|-------------|
| `--rule` / `-r` | Alert rule (repeatable) |
| `--summary` | Print only the summary line, not individual hits |
| `--exit-code` | Exit with code `1` when at least one hit is found (useful in CI) |

## Output

```
[OOM] line 42: 2024-01-15 ERROR out of memory – killed worker
[DISK] line 87: 2024-01-15 ERROR disk full on /var/log

--- alert summary: 2/200 lines matched (1.0%) across 2 rule(s) ---
```

## Python API

```python
from logslice.alerter import build_rules, check_alerts

rules = build_rules(["OOM=out of memory", "DISK=disk full:ERROR"])
result = check_alerts(lines, rules)
print(result.hit_count, result.hit_rate)
```
