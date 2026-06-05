# SIN-Scheduler Skill

[![GitNexus](https://img.shields.io/badge/GitNexus-knowledge%20graph-8B5CF6)](.gitnexus/)
[![CEO Audit](https://img.shields.io/badge/CEO_Audit-passing-success)](.github/workflows/ceo-audit.yml)

> **⚠️ GitNexus-Pflicht:** Bevor du Code in diesem Repo änderst, MUSST du `gitnexus_impact()` (Blast Radius) und `gitnexus_detect_changes()` (vor Commit) ausführen. Siehe [GitNexus Guide](.gitnexus/).

**MCP Server + Python modules for job scheduling with cron and intervals.**

## Features

- **Cron expressions** — full cron syntax via `croniter`
- **Interval scheduling** — human-readable strings (`10m`, `2h`, `1d`)
- **SQLite persistence** — jobs and logs survive restarts
- **Subprocess execution** — timeout, error handling, stdout/stderr capture
- **MCP tools** — 6 tools for agents: `schedule_job`, `schedule_list`, `schedule_cancel`, `schedule_status`, `schedule_run_now`, `schedule_logs`
- **CLI scripts** — start/stop daemon, add/list/remove jobs

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Start daemon
./scripts/scheduler-start.sh

# Add a job
./scripts/scheduler-add.sh -n "backup" -c "pg_dump mydb" -t cron -e "0 2 * * *"

# List jobs
./scripts/scheduler-list.sh

# Stop daemon
./scripts/scheduler-stop.sh
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `schedule_job` | Add a new job |
| `schedule_list` | List all jobs |
| `schedule_cancel` | Cancel a job by ID |
| `schedule_status` | Show job status |
| `schedule_run_now` | Trigger immediately |
| `schedule_logs` | Show recent logs |

## Architecture

```
MCP Client (OpenCode)
    ↓ FastMCP
mcp_server.py
    ↓ JSON
Scheduler (schedule + croniter)
    ↓ SQLite
Persistence (jobs + logs)
    ↓ subprocess
Executor (stdout/stderr/timeout)
```

## Project Structure

```
SIN-Code-Scheduler-Skill/
├── src/sin_scheduler/
│   ├── __init__.py
│   ├── scheduler.py      — Core scheduler
│   ├── jobs.py           — Job dataclass
│   ├── executor.py       — Subprocess execution
│   ├── persistence.py    — SQLite persistence
│   └── mcp_server.py     — FastMCP tools
├── scripts/
│   ├── scheduler-start.sh
│   ├── scheduler-stop.sh
│   ├── scheduler-status.sh
│   ├── scheduler-add.sh
│   ├── scheduler-list.sh
│   └── scheduler-remove.sh
├── tests/
│   ├── test_persistence.py
│   ├── test_jobs.py
│   ├── test_executor.py
│   ├── test_scheduler.py
│   └── test_mcp_server.py
├── .github/workflows/ceo-audit.yml
├── README.md
├── SKILL.md
└── pyproject.toml
```

## Testing

```bash
pytest -q
pytest --cov=src/sin_scheduler --cov-report=term-missing
```

## CoDocs

Every `.py` file has a `.doc.md` companion in the same directory.

## License

MIT — OpenSIN-Code
