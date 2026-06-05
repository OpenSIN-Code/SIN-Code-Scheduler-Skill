# `sin_scheduler/persistence.py`

## What it does
SQLite-backed persistence layer for scheduled jobs and execution logs.
Handles CRUD, filtering, and log retention with thread-safe locking.

## Dependencies
- `sqlite3` (stdlib)
- `threading.RLock` for reentrant lock

## Key classes
- `JobRecord` — dataclass mirroring the `jobs` table schema.
- `LogRecord` — dataclass mirroring the `logs` table schema.
- `Persistence` — main class with `_connection()` context manager.

## Important config
- `DEFAULT_DB_PATH = ~/.sin_scheduler/scheduler.db`
- `days` parameter for `delete_old_logs()` defaults to 30.

## Usage
```python
from sin_scheduler.persistence import Persistence
p = Persistence()
p.save_job(record)
logs = p.get_logs(job_id="abc", limit=10)
```

## Caveats
- SQLite connections are created per call inside `_connection()`; this is
  thread-safe but not optimized for extremely high write throughput.
- `delete_job()` also deletes all associated logs (cascade).
