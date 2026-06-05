# `scripts/scheduler-status.sh`

## What it does
Shows whether the scheduler daemon is running, its PID, and the last few log lines.

## Dependencies
- `kill -0` for PID validity
- `tail` for log preview

## Usage
```bash
./scripts/scheduler-status.sh
```

## Notes
- Also prints the database path for quick reference.
- If the PID file exists but the process is dead, reports "NOT RUNNING (stale PID file)".
