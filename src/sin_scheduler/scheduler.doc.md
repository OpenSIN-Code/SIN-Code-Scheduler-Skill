# `sin_scheduler/scheduler.py`

## What it does
Core scheduler that bridges `schedule` (interval jobs), `croniter` (cron jobs),
persistence, and the executor. Runs a background thread that checks for due jobs
every second.

## Dependencies
- `schedule` library for interval-based scheduling
- `croniter` for cron expression evaluation
- `persistence.py`, `jobs.py`, `executor.py`

## Key methods
- `start()` / `stop()` — lifecycle of the background thread.
- `add_job()` / `remove_job()` — register or cancel jobs.
- `run_job_now()` — immediate manual execution.
- `get_status()` — human-readable status dict with recent logs.

## Usage
```python
from sin_scheduler.scheduler import Scheduler
s = Scheduler()
s.start()
s.add_job(Job(name="backup", command="pg_dump db", job_type="cron", schedule_expr="0 2 * * *"))
```

## Caveats
- `_check_cron_jobs()` evaluates every second; may miss a firing if the machine
  sleeps between checks. For production cron, consider a dedicated cron daemon.
- `_register_interval()` parses human strings like "10m" — not all `schedule`
  library features are exposed.
- `enable_job()` and `disable_job()` mutate the in-memory schedule handles and
  the DB; be careful with concurrent modifications.
