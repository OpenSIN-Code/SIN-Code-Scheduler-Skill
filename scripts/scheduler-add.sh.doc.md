# `scripts/scheduler-add.sh`

## What it does
CLI wrapper to add a job to the scheduler database without using the MCP tools.

## Dependencies
- `python3` with `sin_scheduler` on `PYTHONPATH`
- `getopts` for argument parsing

## Usage
```bash
./scripts/scheduler-add.sh -n "backup" -c "pg_dump db" -t cron -e "0 2 * * *"
./scripts/scheduler-add.sh -n "health" -c "curl -sf http://localhost/health" -t interval -e "5m" -o 30
```

## Options
| Flag | Description |
|------|-------------|
| `-n` | Job name |
| `-c` | Command to execute |
| `-t` | Schedule type (`cron` or `interval`) |
| `-e` | Schedule expression |
| `-o` | Timeout seconds (default: 60) |
| `-d` | Disable the job |

## Notes
- Creates `~/.sin_scheduler/scheduler.db` if it does not exist.
