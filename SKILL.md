---
name: sin-scheduler
description: "Job scheduling with cron and intervals — MCP Server + CLI"
version: 0.1.0
category: automation
requirements:
  - Python >= 3.10
  - schedule >= 1.2.0
  - croniter >= 2.0.0
  - fastmcp >= 0.3.0
---

# SIN-Scheduler Skill

Schedule and manage recurring jobs via cron expressions or human-readable intervals.

## Commands

```bash
# MCP server (stdio transport)
sin-scheduler-mcp

# CLI scripts
./scripts/scheduler-start.sh
./scripts/scheduler-add.sh -n "backup" -c "pg_dump db" -t cron -e "0 2 * * *"
./scripts/scheduler-list.sh
./scripts/scheduler-remove.sh <job_id>
./scripts/scheduler-stop.sh
```

## MCP Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `schedule_job` | name, command, schedule_type, schedule_expr, timeout_seconds, enabled, metadata | job_id |
| `schedule_list` | enabled_only | list of jobs |
| `schedule_cancel` | job_id | removed bool |
| `schedule_status` | job_id | status dict |
| `schedule_run_now` | job_id | execution result |
| `schedule_logs` | job_id, limit, status | list of logs |

## Installation

```bash
git clone https://github.com/OpenSIN-Code/SIN-Code-Scheduler-Skill.git
cd SIN-Code-Scheduler-Skill
pip install -e ".[dev]"
```

## Usage Examples

### Cron job
```python
# Via MCP
schedule_job("backup", "pg_dump mydb", "cron", "0 2 * * *")
```

### Interval job
```python
# Via MCP
schedule_job("health-check", "curl -sf http://localhost/health", "interval", "5m")
```

### Run immediately
```python
schedule_run_now("<job_id>")
```

## Data Storage

- SQLite database at `~/.sin_scheduler/scheduler.db`
- Jobs table: ID, name, command, type, expression, counters, timestamps
- Logs table: execution stdout, stderr, exit code, status, timestamps

## Notes

- The scheduler daemon runs in a background thread.
- Jobs are persisted across restarts.
- Logs are retained for 30 days by default.
