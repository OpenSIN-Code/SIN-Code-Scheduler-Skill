# `tests/test_executor.py`

## What it does
Tests the `Executor` class covering:
- Successful and failed command execution
- Invalid commands and timeout handling
- stdout/stderr capture
- Log ID uniqueness
- Timestamp correctness
- Async execution with callbacks
- Callback exception safety
- Edge cases (empty command, multiline, environment)

## Test classes
- `TestExecutorRunNow` — 8 tests for synchronous execution
- `TestExecutorAsync` — 4 tests for background threads
- `TestExecutorEdgeCases` — 3 tests for boundary conditions

## Notes
- Timeout tests use `sleep 5` with a 1-second timeout; should be fast enough.
- Callback exceptions are silently swallowed to protect the executor.
