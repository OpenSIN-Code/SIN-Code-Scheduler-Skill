"""
Purpose: Test the MCP server tools.
Docs: tests/test_mcp_server.doc.md
"""
import json
import tempfile
from pathlib import Path

import pytest

from sin_scheduler.mcp_server import schedule_job, schedule_list, schedule_cancel, schedule_status, schedule_run_now, schedule_logs


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    monkeypatch.setenv("SIN_SCHEDULER_DB", str(path))
    yield path
    path.unlink(missing_ok=True)


class TestScheduleJob:
    def test_schedule_cron(self):
        result = schedule_job(
            name="backup",
            command="pg_dump mydb",
            schedule_type="cron",
            schedule_expr="0 2 * * *",
        )
        data = json.loads(result)
        assert "job_id" in data
        assert data["name"] == "backup"
        assert data["schedule_type"] == "cron"
        assert data["status"] == "scheduled"

    def test_schedule_interval(self):
        result = schedule_job(
            name="health",
            command="curl -sf http://localhost/health",
            schedule_type="interval",
            schedule_expr="5m",
        )
        data = json.loads(result)
        assert data["schedule_type"] == "interval"
        assert data["schedule_expr"] == "5m"

    def test_schedule_with_timeout(self):
        result = schedule_job(
            name="slow",
            command="sleep 5",
            schedule_type="interval",
            schedule_expr="1h",
            timeout_seconds=10,
        )
        data = json.loads(result)
        assert "job_id" in data

    def test_schedule_disabled(self):
        result = schedule_job(
            name="off",
            command="echo",
            schedule_type="cron",
            schedule_expr="* * * * *",
            enabled=False,
        )
        data = json.loads(result)
        assert data["status"] == "scheduled"


class TestScheduleList:
    def test_empty_list(self):
        result = schedule_list()
        data = json.loads(result)
        assert data == []

    def test_list_with_jobs(self):
        schedule_job(name="a", command="echo a", schedule_type="cron", schedule_expr="* * * * *")
        schedule_job(name="b", command="echo b", schedule_type="interval", schedule_expr="10m")
        result = schedule_list()
        data = json.loads(result)
        assert len(data) == 2

    def test_list_enabled_only(self):
        schedule_job(name="on", command="echo", schedule_type="cron", schedule_expr="* * * * *", enabled=True)
        schedule_job(name="off", command="echo", schedule_type="cron", schedule_expr="* * * * *", enabled=False)
        result = schedule_list(enabled_only=True)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "on"


class TestScheduleCancel:
    def test_cancel_existing(self):
        r = schedule_job(name="del", command="echo", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        result = schedule_cancel(job_id)
        data = json.loads(result)
        assert data["removed"] is True

    def test_cancel_nonexistent(self):
        result = schedule_cancel("nonexistent")
        data = json.loads(result)
        assert data["removed"] is False


class TestScheduleStatus:
    def test_status_existing(self):
        r = schedule_job(name="st", command="echo", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        result = schedule_status(job_id)
        data = json.loads(result)
        assert data["job_id"] == job_id
        assert data["name"] == "st"
        assert "recent_logs" in data

    def test_status_not_found(self):
        result = schedule_status("fake")
        data = json.loads(result)
        assert "error" in data


class TestScheduleRunNow:
    def test_run_now_success(self):
        r = schedule_job(name="run", command="echo hello", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        result = schedule_run_now(job_id)
        data = json.loads(result)
        assert data["status"] == "success"
        assert "hello" in data["stdout"]

    def test_run_now_failure(self):
        r = schedule_job(name="fail", command="exit 1", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        result = schedule_run_now(job_id)
        data = json.loads(result)
        assert data["status"] == "failed"
        assert data["exit_code"] == 1

    def test_run_now_not_found(self):
        result = schedule_run_now("fake")
        data = json.loads(result)
        assert "error" in data


class TestScheduleLogs:
    def test_logs_empty(self):
        result = schedule_logs()
        data = json.loads(result)
        assert data == []

    def test_logs_after_run(self):
        r = schedule_job(name="log", command="echo logtest", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        schedule_run_now(job_id)
        result = schedule_logs(job_id=job_id)
        data = json.loads(result)
        assert len(data) >= 1
        assert data[0]["job_id"] == job_id
        assert "logtest" in data[0]["stdout"]

    def test_logs_filtered(self):
        r = schedule_job(name="logf", command="exit 1", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        schedule_run_now(job_id)
        result = schedule_logs(job_id=job_id, status="failed")
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["status"] == "failed"

    def test_logs_limit(self):
        r = schedule_job(name="logl", command="echo x", schedule_type="cron", schedule_expr="* * * * *")
        job_id = json.loads(r)["job_id"]
        for _ in range(5):
            schedule_run_now(job_id)
        result = schedule_logs(job_id=job_id, limit=2)
        data = json.loads(result)
        assert len(data) == 2

    def test_logs_all_jobs(self):
        r1 = schedule_job(name="a", command="echo a", schedule_type="cron", schedule_expr="* * * * *")
        r2 = schedule_job(name="b", command="echo b", schedule_type="cron", schedule_expr="* * * * *")
        schedule_run_now(json.loads(r1)["job_id"])
        schedule_run_now(json.loads(r2)["job_id"])
        result = schedule_logs()
        data = json.loads(result)
        assert len(data) == 2


class TestScheduleJobMetadata:
    def test_metadata_roundtrip(self):
        meta = json.dumps({"owner": "ci", "project": "api"})
        result = schedule_job(
            name="meta",
            command="echo",
            schedule_type="cron",
            schedule_expr="* * * * *",
            metadata=meta,
        )
        data = json.loads(result)
        assert data["status"] == "scheduled"
