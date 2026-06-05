# `sin_scheduler/__init__.py`

## What it does
Package-level exports for `sin_scheduler`. Exposes the four core classes
(`Scheduler`, `Job`, `JobType`, `Executor`, `Persistence`) so consumers can
`from sin_scheduler import Scheduler` without knowing the internal module names.

## Dependencies
- `scheduler.py` (Scheduler)
- `jobs.py` (Job, JobType)
- `executor.py` (Executor)
- `persistence.py` (Persistence)

## Usage
```python
from sin_scheduler import Scheduler, Job
```

## Notes
- `__version__` is defined here for easy access.
- Keep `__all__` in sync when adding new public symbols.
