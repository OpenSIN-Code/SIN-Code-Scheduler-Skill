"""
Purpose: SQLite persistence layer for jobs and execution logs.
Docs: sin_scheduler/persistence.doc.md
"""
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────
DEFAULT_DB_PATH = Path.home() / ".sin_scheduler" / "scheduler.db"


@dataclass
class JobRecord:
    """Database record for a scheduled job."""
    job_id: str
    name: str
    command: str
    job_type: str  # "cron" or "interval"
    schedule_expr: str
    created_at: str
    updated_at: str
    enabled: int = 1
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0
    failure_count: int = 0
    timeout_seconds: int = 60
    metadata_json: str = "{}"

    def metadata(self) -> dict[str, Any]:
        """Parse metadata_json into a dict."""
        try:
            return json.loads(self.metadata_json)
        except json.JSONDecodeError:
            return {}


@dataclass
class LogRecord:
    """Database record for a single execution log."""
    log_id: str
    job_id: str
    started_at: str
    finished_at: str = ""
    status: str = "pending"  # pending, running, success, failed, timeout
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""


class Persistence:
    """
    SQLite-backed persistence for jobs and execution logs.

    Thread-safe via reentrant lock and per-thread connections.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self._lock = threading.RLock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    schedule_expr TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_run TEXT NOT NULL DEFAULT '',
                    next_run TEXT NOT NULL DEFAULT '',
                    run_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    timeout_seconds INTEGER NOT NULL DEFAULT 60,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    log_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    exit_code INTEGER NOT NULL DEFAULT -1,
                    stdout TEXT NOT NULL DEFAULT '',
                    stderr TEXT NOT NULL DEFAULT '',
                    error_message TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_job_id ON logs(job_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_started_at ON logs(started_at)"
            )
            conn.commit()

    @contextmanager
    def _connection(self):
        """Yield a SQLite connection inside the lock."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            try:
                yield conn
            finally:
                conn.close()

    # ── Job CRUD ──────────────────────────────────────

    def save_job(self, record: JobRecord) -> None:
        """Insert or replace a job record."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    name=excluded.name,
                    command=excluded.command,
                    job_type=excluded.job_type,
                    schedule_expr=excluded.schedule_expr,
                    updated_at=excluded.updated_at,
                    enabled=excluded.enabled,
                    last_run=excluded.last_run,
                    next_run=excluded.next_run,
                    run_count=excluded.run_count,
                    failure_count=excluded.failure_count,
                    timeout_seconds=excluded.timeout_seconds,
                    metadata_json=excluded.metadata_json
                """,
                (
                    record.job_id,
                    record.name,
                    record.command,
                    record.job_type,
                    record.schedule_expr,
                    record.created_at,
                    record.updated_at,
                    record.enabled,
                    record.last_run,
                    record.next_run,
                    record.run_count,
                    record.failure_count,
                    record.timeout_seconds,
                    record.metadata_json,
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> JobRecord | None:
        """Fetch a single job by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def list_jobs(self, enabled_only: bool = False) -> list[JobRecord]:
        """Return all jobs, optionally filtering to enabled ones."""
        query = "SELECT * FROM jobs"
        params: tuple = ()
        if enabled_only:
            query += " WHERE enabled = 1"
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_job(r) for r in rows]

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its logs. Returns True if the job existed."""
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.execute("DELETE FROM logs WHERE job_id = ?", (job_id,))
            conn.commit()
            return cur.rowcount > 0

    def update_job_stats(
        self,
        job_id: str,
        last_run: str | None = None,
        next_run: str | None = None,
        run_count: int | None = None,
        failure_count: int | None = None,
        enabled: int | None = None,
    ) -> None:
        """Update mutable statistics for a job."""
        fields = []
        values = []
        if last_run is not None:
            fields.append("last_run = ?")
            values.append(last_run)
        if next_run is not None:
            fields.append("next_run = ?")
            values.append(next_run)
        if run_count is not None:
            fields.append("run_count = ?")
            values.append(run_count)
        if failure_count is not None:
            fields.append("failure_count = ?")
            values.append(failure_count)
        if enabled is not None:
            fields.append("enabled = ?")
            values.append(enabled)
        if not fields:
            return
        values.append(job_id)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?",
                values,
            )
            conn.commit()

    # ── Log CRUD ──────────────────────────────────────

    def save_log(self, record: LogRecord) -> None:
        """Insert or replace a log record."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(log_id) DO UPDATE SET
                    finished_at=excluded.finished_at,
                    status=excluded.status,
                    exit_code=excluded.exit_code,
                    stdout=excluded.stdout,
                    stderr=excluded.stderr,
                    error_message=excluded.error_message
                """,
                (
                    record.log_id,
                    record.job_id,
                    record.started_at,
                    record.finished_at,
                    record.status,
                    record.exit_code,
                    record.stdout,
                    record.stderr,
                    record.error_message,
                ),
            )
            conn.commit()

    def get_logs(
        self,
        job_id: str | None = None,
        limit: int = 100,
        status: str | None = None,
    ) -> list[LogRecord]:
        """Fetch recent logs, optionally filtered by job_id or status."""
        query = "SELECT * FROM logs WHERE 1=1"
        params: list = []
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_log(r) for r in rows]

    def delete_old_logs(self, days: int = 30) -> int:
        """Delete logs older than N days. Returns count deleted."""
        cutoff = datetime.now().isoformat()
        with self._connection() as conn:
            cur = conn.execute(
                "DELETE FROM logs WHERE started_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            conn.commit()
            return cur.rowcount

    def _row_to_job(self, row: tuple) -> JobRecord:
        """Convert a SQLite row tuple into a JobRecord."""
        return JobRecord(
            job_id=row[0],
            name=row[1],
            command=row[2],
            job_type=row[3],
            schedule_expr=row[4],
            created_at=row[5],
            updated_at=row[6],
            enabled=row[7],
            last_run=row[8],
            next_run=row[9],
            run_count=row[10],
            failure_count=row[11],
            timeout_seconds=row[12],
            metadata_json=row[13],
        )

    def _row_to_log(self, row: tuple) -> LogRecord:
        """Convert a SQLite row tuple into a LogRecord."""
        return LogRecord(
            log_id=row[0],
            job_id=row[1],
            started_at=row[2],
            finished_at=row[3],
            status=row[4],
            exit_code=row[5],
            stdout=row[6],
            stderr=row[7],
            error_message=row[8],
        )
