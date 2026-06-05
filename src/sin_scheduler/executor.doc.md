# `sin_scheduler/executor.py`

## What it does
Runs shell commands via `subprocess.run` with timeout support, captures stdout/stderr,
and returns structured `ExecutionResult` objects. Also supports async execution via
background threads.

## Dependencies
- `subprocess` (stdlib)
- `threading` for `run_async()`

## Key classes
- `ExecutionResult` — dataclass with stdout, stderr, exit_code, status, timestamps.
- `Executor` — `run_now()` and `run_async()` methods.

## Usage
```python
from sin_scheduler.executor import Executor
ex = Executor(default_timeout=30)
result = ex.run_now("job-1", "echo hello", timeout=10)
assert result.status == "success"
```

## Caveats
- `timeout` is passed to `subprocess.run(..., timeout=…)`; kills the process on expiry.
- Callback exceptions in `run_async()` are silently swallowed to prevent executor crashes.
- The process tree is not fully killed on timeout (only the direct process).
