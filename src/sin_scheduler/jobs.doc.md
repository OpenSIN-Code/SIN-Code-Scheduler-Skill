# `sin_scheduler/jobs.py`

## What it does
Defines the `Job` dataclass and the `JobType` enum used throughout the scheduler.
Provides serialization helpers (`to_record()` / `from_record()`) for the
persistence layer.

## Dependencies
- `uuid` for auto-generating job IDs
- `json` for metadata serialization

## Key classes
- `JobType` — Enum with `CRON` and `INTERVAL`.
- `Job` — Core dataclass with fields for schedule, command, counters, metadata.

## Usage
```python
from sin_scheduler.jobs import Job
job = Job(name="backup", command="pg_dump db", job_type="cron", schedule_expr="0 2 * * *")
```

## Notes
- `bump_run()` updates `run_count`/`failure_count` and `last_run`/`updated_at`.
- `metadata` is stored as JSON in SQLite; use `json.dumps`/`json.loads`.
