# `tests/test_mcp_server.py`

## What it does
Tests the FastMCP tools exposed in `mcp_server.py` covering:
- `schedule_job` with cron and interval types
- `schedule_list` with and without filters
- `schedule_cancel` for existing and missing jobs
- `schedule_status` for existing and missing jobs
- `schedule_run_now` success and failure paths
- `schedule_logs` with filtering and limits
- Metadata roundtrip

## Fixtures
- `temp_db` — auto-injected via `monkeypatch` on `SIN_SCHEDULER_DB`

## Test classes
- `TestScheduleJob` — 4 tests
- `TestScheduleList` — 3 tests
- `TestScheduleCancel` — 2 tests
- `TestScheduleStatus` — 2 tests
- `TestScheduleRunNow` — 3 tests
- `TestScheduleLogs` — 5 tests
- `TestScheduleJobMetadata` — 1 test

## Notes
- All tool returns are JSON strings; tests `json.loads` the result.
- Errors are returned as JSON with `"error"` key rather than raising.
