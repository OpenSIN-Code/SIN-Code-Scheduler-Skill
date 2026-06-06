"""
Purpose: Test Job dataclass and serialization.
Docs: test_jobs.doc.md
"""
import json

import pytest

from sin_scheduler.jobs import Job, JobType


class TestJobCreation:
    def test_job_defaults(self):
        j = Job()
        assert j.name == ""
        assert j.command == ""
        assert j.job_type == "cron"
        assert j.enabled is True
        assert j.run_count == 0
        assert j.failure_count == 0
        assert j.timeout_seconds == 60
        assert j.metadata == {}

    def test_job_with_values(self):
        j = Job(
            name="backup",
            command="pg_dump db",
            job_type="interval",
            schedule_expr="1h",
            timeout_seconds=300,
            enabled=False,
            metadata={"db": "postgres"},
        )
        assert j.name == "backup"
        assert j.job_type == "interval"
        assert j.schedule_expr == "1h"
        assert j.timeout_seconds == 300
        assert j.enabled is False
        assert j.metadata == {"db": "postgres"}

    def test_job_generates_uuid(self):
        j1 = Job()
        j2 = Job()
        assert j1.job_id != j2.job_id
        assert len(j1.job_id) == 36


class TestJobSerialization:
    def test_to_record(self):
        j = Job(
            name="test",
            command="echo hi",
            job_type="cron",
            schedule_expr="0 9 * * *",
            timeout_seconds=120,
            metadata={"foo": "bar"},
        )
        rec = j.to_record()
        assert rec["name"] == "test"
        assert rec["command"] == "echo hi"
        assert rec["job_type"] == "cron"
        assert rec["schedule_expr"] == "0 9 * * *"
        assert rec["timeout_seconds"] == 120
        assert rec["enabled"] == 1
        assert json.loads(rec["metadata_json"]) == {"foo": "bar"}

    def test_from_record(self):
        rec = {
            "job_id": "abc",
            "name": "rec",
            "command": "echo",
            "job_type": "interval",
            "schedule_expr": "10m",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "enabled": 0,
            "last_run": "2024-01-02T00:00:00",
            "next_run": "",
            "run_count": 3,
            "failure_count": 1,
            "timeout_seconds": 90,
            "metadata_json": '{"key": "val"}',
        }
        j = Job.from_record(rec)
        assert j.job_id == "abc"
        assert j.name == "rec"
        assert j.enabled is False
        assert j.run_count == 3
        assert j.failure_count == 1
        assert j.timeout_seconds == 90
        assert j.metadata == {"key": "val"}

    def test_roundtrip(self):
        j = Job(
            name="round",
            command="ls",
            job_type="cron",
            schedule_expr="0 0 * * *",
            metadata={"x": 1},
        )
        rec = j.to_record()
        j2 = Job.from_record(rec)
        assert j2.name == j.name
        assert j2.command == j.command
        assert j2.metadata == j.metadata


class TestJobBumpRun:
    def test_bump_success(self):
        j = Job()
        j.bump_run(success=True)
        assert j.run_count == 1
        assert j.failure_count == 0
        assert j.last_run != ""

    def test_bump_failure(self):
        j = Job()
        j.bump_run(success=False)
        assert j.run_count == 0
        assert j.failure_count == 1

    def test_bump_updates_updated_at(self):
        j = Job()
        old = j.updated_at
        j.bump_run(success=True)
        assert j.updated_at != old


class TestJobTypeEnum:
    def test_cron_value(self):
        assert JobType.CRON.value == "cron"

    def test_interval_value(self):
        assert JobType.INTERVAL.value == "interval"
