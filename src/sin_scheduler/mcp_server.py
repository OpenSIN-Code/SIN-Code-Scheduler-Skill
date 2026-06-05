"""
Purpose: FastMCP server exposing scheduler tools for agents.
Docs: sin_scheduler/mcp_server.doc.md
"""
import json
import os
from pathlib import Path

from fastmcp import FastMCP

from .executor import Executor
from .jobs import Job
from .persistence import Persistence
from .scheduler import Scheduler

mcp = FastMCP("sin_scheduler")

# Global singletons — re-created per tool call to stay stateless

def _get_scheduler() -> Scheduler:
    """Instantiate a Scheduler with default persistence."""
    db_path = os.getenv("SIN_SCHEDULER_DB")
    persistence = Persistence(db_path=Path(db_path) if db_path else None)
    return Scheduler(persistence=persistence)


@mcp.tool()
def schedule_job(
    name: str,
    command: str,
    schedule_type: str,
    schedule_expr: str,
    timeout_seconds: int = 60,
    enabled: bool = True,
    metadata: str = "{}",
) -> str:
    """
    Schedule a new job.

    Args:
        name: Human-readable job name.
        command: Shell command to execute.
        schedule_type: "cron" or "interval".
        schedule_expr: Cron string (e.g. "0 9 * * *") or interval (e.g. "10m").
        timeout_seconds: Max execution time before killing.
        enabled: Whether the job is active immediately.
        metadata: JSON string of arbitrary metadata.

    Returns:
        JSON string with job_id and confirmation.
    """
    scheduler = _get_scheduler()
    job = Job(
        name=name,
        command=command,
        job_type=schedule_type,
        schedule_expr=schedule_expr,
        timeout_seconds=timeout_seconds,
        enabled=enabled,
        metadata=json.loads(metadata),
    )
    job_id = scheduler.add_job(job)
    return json.dumps(
        {
            "job_id": job_id,
            "name": name,
            "schedule_type": schedule_type,
            "schedule_expr": schedule_expr,
            "status": "scheduled",
        }
    )


@mcp.tool()
def schedule_list(enabled_only: bool = False) -> str:
    """
    List all scheduled jobs.

    Args:
        enabled_only: If True, only return enabled jobs.

    Returns:
        JSON string list of jobs.
    """
    scheduler = _get_scheduler()
    jobs = scheduler.list_jobs(enabled_only=enabled_only)
    return json.dumps(
        [
            {
                "job_id": j.job_id,
                "name": j.name,
                "command": j.command,
                "job_type": j.job_type,
                "schedule_expr": j.schedule_expr,
                "enabled": j.enabled,
                "last_run": j.last_run,
                "next_run": j.next_run,
                "run_count": j.run_count,
                "failure_count": j.failure_count,
                "timeout_seconds": j.timeout_seconds,
            }
            for j in jobs
        ]
    )


@mcp.tool()
def schedule_cancel(job_id: str) -> str:
    """
    Cancel and remove a scheduled job.

    Args:
        job_id: The ID of the job to cancel.

    Returns:
        JSON string with success status.
    """
    scheduler = _get_scheduler()
    removed = scheduler.remove_job(job_id)
    return json.dumps({"job_id": job_id, "removed": removed})


@mcp.tool()
def schedule_status(job_id: str) -> str:
    """
    Show job status including last run, next run, and failures.

    Args:
        job_id: The ID of the job to inspect.

    Returns:
        JSON string with status details.
    """
    scheduler = _get_scheduler()
    try:
        status = scheduler.get_status(job_id)
        return json.dumps(status)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def schedule_run_now(job_id: str) -> str:
    """
    Trigger a job immediately, regardless of schedule.

    Args:
        job_id: The ID of the job to run.

    Returns:
        JSON string with execution result.
    """
    scheduler = _get_scheduler()
    try:
        result = scheduler.run_job_now(job_id)
        return json.dumps(
            {
                "job_id": job_id,
                "status": result.status,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error_message": result.error_message,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
            }
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def schedule_logs(job_id: str | None = None, limit: int = 50, status: str = "") -> str:
    """
    Show recent job execution logs.

    Args:
        job_id: Optional filter by job ID.
        limit: Maximum number of logs to return.
        status: Optional filter by status (pending, running, success, failed, timeout).

    Returns:
        JSON string list of log entries.
    """
    scheduler = _get_scheduler()
    logs = scheduler.get_logs(
        job_id=job_id,
        limit=limit,
        status=status or None,
    )
    return json.dumps(
        [
            {
                "log_id": l.log_id,
                "job_id": l.job_id,
                "started_at": l.started_at,
                "finished_at": l.finished_at,
                "status": l.status,
                "exit_code": l.exit_code,
                "stdout": l.stdout,
                "stderr": l.stderr,
                "error_message": l.error_message,
            }
            for l in logs
        ]
    )


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
