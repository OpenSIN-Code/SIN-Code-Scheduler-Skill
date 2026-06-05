# `scripts/scheduler-list.sh`

## What it does
Lists all scheduled jobs in a human-readable pipe-delimited format.

## Dependencies
- `python3` with `sin_scheduler` on `PYTHONPATH`

## Usage
```bash
./scripts/scheduler-list.sh
```

## Notes
- Shows `job_id`, `name`, `type`, `expr`, `enabled`, `run_count`, `failure_count`.
- If no jobs exist, prints "No jobs scheduled".
