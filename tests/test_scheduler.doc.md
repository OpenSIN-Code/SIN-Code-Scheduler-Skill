# `tests/test_scheduler.py`

## What it does
Tests the `Scheduler` class covering:
- Lifecycle (start, stop, double start/stop)
- Job registration and removal
- Interval parsing (seconds, minutes, hours, days)
- Invalid interval handling
- Cron expression acceptance
- Immediate execution (`run_job_now`)
- Status retrieval
- Enable/disable toggling
- Log retrieval and filtering
- Persistence across scheduler instances

## Fixtures
- `temp_db` — temporary SQLite path
- `scheduler` — started `Scheduler` instance with temp DB

## Test classes
- `TestSchedulerLifecycle` — 4 tests
- `TestSchedulerAddRemove` — 8 tests
- `TestSchedulerIntervalParsing` — 7 tests
- `TestSchedulerCron` — 2 tests
- `TestSchedulerRunNow` — 5 tests
- `TestSchedulerStatus` — 2 tests
- `TestSchedulerEnableDisable` — 4 tests
- `TestSchedulerLogs` — 3 tests
- `TestSchedulerPersistence` — 1 test

## Notes
- `scheduler` fixture auto-stops after each test to prevent daemon leaks.
- `run_job_now` blocks until execution completes; fine for tests.
