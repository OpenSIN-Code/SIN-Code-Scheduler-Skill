# `sin_scheduler/mcp_server.py`

## What it does
FastMCP server exposing six scheduler tools to MCP clients (e.g., OpenCode).
Each tool is stateless: it creates a fresh `Scheduler` + `Persistence` per call.

## Dependencies
- `fastmcp` for the MCP framework
- `scheduler.py`, `persistence.py`, `jobs.py`

## Tools exposed
| Tool | Purpose |
|------|---------|
| `schedule_job` | Add a new job |
| `schedule_list` | List all jobs |
| `schedule_cancel` | Remove a job |
| `schedule_status` | Inspect job status |
| `schedule_run_now` | Execute immediately |
| `schedule_logs` | View recent logs |

## Usage
```bash
python -m sin_scheduler.mcp_server
# or via entry point: sin-scheduler-mcp
```

## Environment
- `SIN_SCHEDULER_DB` — optional path to SQLite database.

## Notes
- All tool parameters are JSON-serialized strings for MCP compatibility.
- `schedule_job` accepts `metadata` as a JSON string.
- Errors are returned as JSON with an `"error"` key rather than raising exceptions.
