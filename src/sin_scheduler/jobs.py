"""
Purpose: Job definitions and type system for the scheduler.
Docs: sin_scheduler/jobs.doc.md
"""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobType(Enum):
    """Supported scheduling strategies."""
    CRON = "cron"
    INTERVAL = "interval"


@dataclass
class Job:
    """
    Represents a scheduled job.

    Attributes:
        job_id: Unique identifier (UUID4).
        name: Human-readable name.
        command: Shell command to execute.
        job_type: Cron or interval-based.
        schedule_expr: Cron string or interval string (e.g. "10m", "1h").
        created_at: ISO timestamp when the job was created.
        updated_at: ISO timestamp of last modification.
        enabled: Whether the job is active.
        last_run: ISO timestamp of last execution.
        next_run: ISO timestamp of next scheduled execution.
        run_count: Total successful executions.
        failure_count: Total failed executions.
        timeout_seconds: Maximum execution time allowed.
        metadata: Arbitrary key-value metadata.
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    command: str = ""
    job_type: str = "cron"
    schedule_expr: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    enabled: bool = True
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0
    failure_count: int = 0
    timeout_seconds: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        """Serialize to a dict compatible with Persistence."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "command": self.command,
            "job_type": self.job_type,
            "schedule_expr": self.schedule_expr,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": 1 if self.enabled else 0,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "timeout_seconds": self.timeout_seconds,
            "metadata_json": json.dumps(self.metadata),
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Job":
        """Deserialize from a Persistence record dict."""
        return cls(
            job_id=record["job_id"],
            name=record["name"],
            command=record["command"],
            job_type=record["job_type"],
            schedule_expr=record["schedule_expr"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            enabled=bool(record["enabled"]),
            last_run=record["last_run"],
            next_run=record["next_run"],
            run_count=record["run_count"],
            failure_count=record["failure_count"],
            timeout_seconds=record["timeout_seconds"],
            metadata=json.loads(record.get("metadata_json", "{}")),
        )

    def bump_run(self, success: bool = True) -> None:
        """Increment run counters and update timestamps."""
        self.updated_at = datetime.now().isoformat()
        if success:
            self.run_count += 1
            self.last_run = self.updated_at
        else:
            self.failure_count += 1
