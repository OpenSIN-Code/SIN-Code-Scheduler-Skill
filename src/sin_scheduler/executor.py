"""
Purpose: Job execution engine with subprocess, timeout, and error handling.
Docs: executor.doc.md
"""
import subprocess
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ExecutionResult:
    """Result of a single job execution."""
    log_id: str
    job_id: str
    started_at: str
    finished_at: str
    status: str
    exit_code: int
    stdout: str
    stderr: str
    error_message: str


class Executor:
    """
    Runs shell commands with timeout support and captures output.

    Thread-safe: each run_now() call is independent.
    """

    def __init__(self, default_timeout: int = 60) -> None:
        self.default_timeout = default_timeout

    def run_now(
        self,
        job_id: str,
        command: str,
        timeout: int | None = None,
    ) -> ExecutionResult:
        """
        Execute a command immediately.

        Args:
            job_id: The job identifier for log correlation.
            command: Shell command to run.
            timeout: Seconds to wait before killing. Defaults to default_timeout.

        Returns:
            ExecutionResult with stdout, stderr, exit_code, and status.
        """
        log_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()
        timeout = timeout or self.default_timeout

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            finished_at = datetime.now().isoformat()
            status = "success" if proc.returncode == 0 else "failed"
            return ExecutionResult(
                log_id=log_id,
                job_id=job_id,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                error_message="",
            )
        except subprocess.TimeoutExpired as exc:
            finished_at = datetime.now().isoformat()
            # subprocess.run already kills the process on timeout
            return ExecutionResult(
                log_id=log_id,
                job_id=job_id,
                started_at=started_at,
                finished_at=finished_at,
                status="timeout",
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                error_message=f"Timeout after {timeout} seconds",
            )
        except Exception as exc:
            finished_at = datetime.now().isoformat()
            return ExecutionResult(
                log_id=log_id,
                job_id=job_id,
                started_at=started_at,
                finished_at=finished_at,
                status="failed",
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=str(exc),
            )

    def run_async(
        self,
        job_id: str,
        command: str,
        timeout: int | None = None,
        callback: Any | None = None,
    ) -> threading.Thread:
        """
        Execute a command in a background thread.

        Args:
            job_id: Job identifier.
            command: Shell command.
            timeout: Seconds before killing.
            callback: Optional callable(result: ExecutionResult) invoked on completion.

        Returns:
            The running Thread object.
        """
        thread = threading.Thread(
            target=self._run_with_callback,
            args=(job_id, command, timeout, callback),
            daemon=True,
        )
        thread.start()
        return thread

    def _run_with_callback(
        self,
        job_id: str,
        command: str,
        timeout: int | None,
        callback: Any | None,
    ) -> None:
        """Internal wrapper that invokes the callback after execution."""
        result = self.run_now(job_id, command, timeout)
        if callback is not None:
            try:
                callback(result)
            except Exception:
                pass  # caller's callback must not crash the executor
