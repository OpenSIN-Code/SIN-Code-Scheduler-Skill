# `scripts/scheduler-stop.sh`

## What it does
Reads the PID file and gracefully (then forcefully) stops the scheduler daemon.

## Dependencies
- `kill` for process signaling

## Usage
```bash
./scripts/scheduler-stop.sh
```

## Notes
- Removes the PID file after stopping.
- If the PID file is stale, prints a message and cleans up.
- Force-kill (`kill -9`) is used as a fallback after 1 second.
