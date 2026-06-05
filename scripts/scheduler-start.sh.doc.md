# `scripts/scheduler-start.sh`

## What it does
Starts the SIN-Scheduler daemon in the background using a Python one-liner
that imports the `Scheduler` and `Persistence` classes and runs a sleep loop.

## Dependencies
- `python3` with `sin_scheduler` on `PYTHONPATH`
- `nohup` for backgrounding

## Usage
```bash
./scripts/scheduler-start.sh
```

## Notes
- PID is written to `~/.sin_scheduler/scheduler.pid`.
- Logs go to `~/.sin_scheduler/scheduler.log`.
- If the scheduler is already running, exits silently.
- The Python one-liner is inline; edit it if you need custom DB paths.
