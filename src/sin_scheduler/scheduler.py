"""
Purpose: Core scheduler combining schedule/croniter with persistence and execution.
Docs: scheduler.doc.md
"""
import threading
import time
import uuid
from datetime import datetime
from typing import Any

import schedule
from croniter import croniter

from .executor import Executor, ExecutionResult
from .jobs import Job
from .persistence import JobRecord, LogRecord, Persistence


class Scheduler:
    """
    Background scheduler that runs jobs via cron or interval expressions.

    Uses the `schedule` library for interval jobs and `croniter` for cron jobs.
    A background thread calls run_pending() every second.
    """

    def __init__(
        self,
        persistence: Persistence | None = None,
        executor: Executor | None = None,
    ) -> None:
        self.persistence = persistence or Persistence()
        self.executor = executor or Executor()
        self._jobs: dict[str, schedule.Job] = {}  # schedule library handles
        self._cron_expressions: dict[str, str] = {}  # job_id -> cron string
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

    # ── Lifecycle ──────────────────────────────────────

    def start(self) -> None:
        """Start the background scheduler thread."""
        with self._lock:
            if self._running:
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self._running = True

    def stop(self) -> None:
        """Signal the scheduler thread to stop and wait for it."""
        with self._lock:
            if not self._running:
                return
            self._stop_event.set()
            self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def is_running(self) -> bool:
        """Return True if the scheduler thread is active."""
        with self._lock:
            return self._running

    def _loop(self) -> None:
        """Internal loop: check pending jobs every second."""
        while not self._stop_event.is_set():
            schedule.run_pending()
            self._check_cron_jobs()
            time.sleep(1)

    # ── Job Registration ──────────────────────────────

    def add_job(self, job: Job) -> str:
        """
        Register a job with the scheduler and persist it.

        Args:
            job: Job instance to schedule.

        Returns:
            The job_id.
        """
        job_id = job.job_id
        self.persistence.save_job(JobRecord(**job.to_record()))

        if not job.enabled:
            return job_id

        with self._lock:
            if job.job_type == "interval":
                self._register_interval(job_id, job.schedule_expr)
            elif job.job_type == "cron":
                self._cron_expressions[job_id] = job.schedule_expr
            else:
                raise ValueError(f"Unsupported job_type: {job.job_type}")
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """
        Cancel a job and remove it from persistence.

        Args:
            job_id: ID of the job to cancel.

        Returns:
            True if the job existed and was removed.
        """
        with self._lock:
            if job_id in self._jobs:
                schedule.cancel_job(self._jobs[job_id])
                del self._jobs[job_id]
            self._cron_expressions.pop(job_id, None)
        return self.persistence.delete_job(job_id)

    def list_jobs(self, enabled_only: bool = False) -> list[Job]:
        """Return all registered jobs."""
        records = self.persistence.list_jobs(enabled_only=enabled_only)
        return [Job.from_record(r.__dict__) for r in records]

    def get_job(self, job_id: str) -> Job | None:
        """Return a single job by ID, or None if not found."""
        record = self.persistence.get_job(job_id)
        if record is None:
            return None
        return Job.from_record(record.__dict__)

    def run_job_now(self, job_id: str) -> ExecutionResult:
        """
        Trigger a job immediately regardless of schedule.

        Args:
            job_id: ID of the job to run.

        Returns:
            ExecutionResult from the run.
        """
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        result = self.executor.run_now(
            job_id, job.command, timeout=job.timeout_seconds
        )
        self._persist_result(job, result)
        return result

    def get_status(self, job_id: str) -> dict[str, Any]:
        """
        Return status information for a job.

        Includes last run, next run, failure count, and recent logs.
        """
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        logs = self.persistence.get_logs(job_id=job_id, limit=5)
        return {
            "job_id": job.job_id,
            "name": job.name,
            "enabled": job.enabled,
            "last_run": job.last_run,
            "next_run": self._calculate_next_run(job),
            "run_count": job.run_count,
            "failure_count": job.failure_count,
            "recent_logs": [
                {
                    "log_id": l.log_id,
                    "started_at": l.started_at,
                    "status": l.status,
                    "exit_code": l.exit_code,
                }
                for l in logs
            ],
        }

    def get_logs(
        self,
        job_id: str | None = None,
        limit: int = 100,
        status: str | None = None,
    ) -> list[LogRecord]:
        """Return recent logs, optionally filtered."""
        return self.persistence.get_logs(job_id=job_id, limit=limit, status=status)

    def enable_job(self, job_id: str) -> bool:
        """Enable a previously disabled job."""
        job = self.get_job(job_id)
        if job is None:
            return False
        job.enabled = True
        self.persistence.update_job_stats(job_id, enabled=1)
        self.add_job(job)
        return True

    def disable_job(self, job_id: str) -> bool:
        """Disable a job without deleting it."""
        job = self.get_job(job_id)
        if job is None:
            return False
        job.enabled = False
        self.persistence.update_job_stats(job_id, enabled=0)
        with self._lock:
            if job_id in self._jobs:
                schedule.cancel_job(self._jobs[job_id])
                del self._jobs[job_id]
            self._cron_expressions.pop(job_id, None)
        return True

    # ── Internal helpers ──────────────────────────────

    def _register_interval(self, job_id: str, expr: str) -> None:
        """Map a human-readable interval to schedule.every()."""
        # Parse expressions like "10s", "5m", "1h", "2d"
        expr = expr.strip().lower()
        if not expr:
            raise ValueError("Empty interval expression")
        value = int("".join(c for c in expr if c.isdigit()) or "0")
        unit = "".join(c for c in expr if not c.isdigit())
        if value <= 0:
            raise ValueError(f"Invalid interval value: {expr}")

        handler = schedule.every(value)
        if unit in ("s", "sec", "seconds"):
            handler = handler.seconds
        elif unit in ("m", "min", "minutes"):
            handler = handler.minutes
        elif unit in ("h", "hr", "hours"):
            handler = handler.hours
        elif unit in ("d", "day", "days"):
            handler = handler.days
        else:
            raise ValueError(f"Unknown interval unit: {unit}")

        scheduled = handler.do(self._on_trigger, job_id)
        self._jobs[job_id] = scheduled

    def _check_cron_jobs(self) -> None:
        """Evaluate cron expressions and trigger jobs when due."""
        now = datetime.now()
        for job_id, expr in list(self._cron_expressions.items()):
            job = self.get_job(job_id)
            if job is None or not job.enabled:
                continue
            try:
                itr = croniter(expr, now)
                next_run = itr.get_next(datetime)
                # If next_run is within 1 second of now, trigger
                if (next_run - now).total_seconds() <= 1:
                    self._on_trigger(job_id)
            except Exception:
                # Bad cron expression — skip
                pass

    def _on_trigger(self, job_id: str) -> None:
        """Called when a job's schedule fires."""
        job = self.get_job(job_id)
        if job is None or not job.enabled:
            return

        def on_complete(result: ExecutionResult) -> None:
            self._persist_result(job, result)

        self.executor.run_async(
            job_id, job.command, timeout=job.timeout_seconds, callback=on_complete
        )

    def _persist_result(self, job: Job, result: ExecutionResult) -> None:
        """Write execution result to persistence and update job stats."""
        self.persistence.save_log(LogRecord(**result.__dict__))
        job.bump_run(success=(result.status == "success"))
        self.persistence.save_job(JobRecord(**job.to_record()))

    def _calculate_next_run(self, job: Job) -> str:
        """Calculate next scheduled execution time for a job."""
        if not job.enabled:
            return ""
        try:
            now = datetime.now()
            if job.job_type == "cron":
                return croniter(job.schedule_expr, now).get_next(datetime).isoformat()
            elif job.job_type == "interval":
                # Reconstruct the interval from the schedule library handle
                handle = self._jobs.get(job.job.job_id)
                if handle:
                    nxt = schedule.next_run(handle)
                    if nxt:
                        return nxt.isoformat()
            return ""
        except Exception:
            return ""
