# `tests/test_persistence.py`

## What it does
Tests the SQLite persistence layer (`Persistence` class) covering:
- Job CRUD (save, get, list, delete, update)
- Log CRUD (save, get filtered, limit, delete old)
- Metadata serialization
- Cascade deletion

## Fixtures
- `db_path` — temporary SQLite file
- `persistence` — `Persistence` instance pointing to the temp DB

## Test classes
- `TestPersistenceJobs` — 7 tests for job operations
- `TestPersistenceLogs` — 5 tests for log operations

## Notes
- Each test runs against a fresh DB; no cross-test contamination.
- `delete_job` cascades to logs; verified in `test_delete_job_cascades_logs`.
