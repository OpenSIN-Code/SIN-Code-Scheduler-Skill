"""
Purpose: Test the Persistence layer (SQLite CRUD for jobs and logs).
Docs: tests/test_persistence.doc.md
"""
import json
import tempfile
from pathlib import Path

import pytest

from sin_scheduler.persistence import JobRecord, LogRecord, Persistence


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def persistence(db_path):
    return Persistence(db_path=db_path)


class TestPersistenceJobs:
    def test_save_and_get_job(self, persistence):
        job = JobRecord(
            job_id="j1",
            name="test",
            command="echo hi",
            job_type="cron",
            schedule_expr="* * * * *",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        persistence.save_job(job)
        fetched = persistence.get_job("j1")
        assert fetched is not None
        assert fetched.name == "test"
        assert fetched.command == "echo hi"
        assert fetched.job_type == "cron"

    def test_get_job_not_found(self, persistence):
        assert persistence.get_job("nonexistent") is None

    def test_list_jobs(self, persistence):
        for i in range(3):
            persistence.save_job(
                JobRecord(
                    job_id=f"j{i}",
                    name=f"job{i}",
                    command="echo",
                    job_type="interval",
                    schedule_expr="5m",
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00",
                    enabled=1 if i < 2 else 0,
                )
            )
        all_jobs = persistence.list_jobs()
        assert len(all_jobs) == 3
        enabled = persistence.list_jobs(enabled_only=True)
        assert len(enabled) == 2

    def test_delete_job(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="del",
                name="del",
                command="echo",
                job_type="cron",
                schedule_expr="0 0 * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        assert persistence.delete_job("del") is True
        assert persistence.get_job("del") is None
        assert persistence.delete_job("del") is False

    def test_update_job_stats(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="upd",
                name="upd",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                run_count=0,
                failure_count=0,
            )
        )
        persistence.update_job_stats(
            "upd", last_run="2024-01-02T00:00:00", run_count=5, failure_count=1
        )
        fetched = persistence.get_job("upd")
        assert fetched.last_run == "2024-01-02T00:00:00"
        assert fetched.run_count == 5
        assert fetched.failure_count == 1

    def test_job_metadata(self, persistence):
        meta = {"key": "value", "number": 42}
        persistence.save_job(
            JobRecord(
                job_id="meta",
                name="meta",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                metadata_json=json.dumps(meta),
            )
        )
        fetched = persistence.get_job("meta")
        assert fetched.metadata() == meta

    def test_save_job_overwrites(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="ow",
                name="old",
                command="echo old",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        persistence.save_job(
            JobRecord(
                job_id="ow",
                name="new",
                command="echo new",
                job_type="interval",
                schedule_expr="10m",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-02T00:00:00",
            )
        )
        fetched = persistence.get_job("ow")
        assert fetched.name == "new"
        assert fetched.job_type == "interval"


class TestPersistenceLogs:
    def test_save_and_get_logs(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="jlog",
                name="log",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        log = LogRecord(
            log_id="l1",
            job_id="jlog",
            started_at="2024-01-01T00:00:00",
            finished_at="2024-01-01T00:00:01",
            status="success",
            exit_code=0,
            stdout="hello",
            stderr="",
            error_message="",
        )
        persistence.save_log(log)
        logs = persistence.get_logs(job_id="jlog")
        assert len(logs) == 1
        assert logs[0].status == "success"
        assert logs[0].stdout == "hello"

    def test_get_logs_filtered_by_status(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="jlog2",
                name="log2",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        for i, status in enumerate(["success", "failed", "success"]):
            persistence.save_log(
                LogRecord(
                    log_id=f"l{i}",
                    job_id="jlog2",
                    started_at=f"2024-01-0{i+1}T00:00:00",
                    finished_at=f"2024-01-0{i+1}T00:00:01",
                    status=status,
                    exit_code=0 if status == "success" else 1,
                    stdout="",
                    stderr="",
                    error_message="",
                )
            )
        success_logs = persistence.get_logs(job_id="jlog2", status="success")
        assert len(success_logs) == 2

    def test_get_logs_limit(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="jlog3",
                name="log3",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        for i in range(10):
            persistence.save_log(
                LogRecord(
                    log_id=f"l{i}",
                    job_id="jlog3",
                    started_at=f"2024-01-{i+1:02d}T00:00:00",
                    status="success",
                    exit_code=0,
                    stdout="",
                    stderr="",
                    error_message="",
                )
            )
        logs = persistence.get_logs(job_id="jlog3", limit=3)
        assert len(logs) == 3
        # Should be ordered newest first
        assert logs[0].log_id == "l9"

    def test_delete_old_logs(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="jold",
                name="old",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        persistence.save_log(
            LogRecord(
                log_id="old1",
                job_id="jold",
                started_at="2020-01-01T00:00:00",
                status="success",
                exit_code=0,
                stdout="",
                stderr="",
                error_message="",
            )
        )
        persistence.save_log(
            LogRecord(
                log_id="new1",
                job_id="jold",
                started_at="2099-01-01T00:00:00",
                status="success",
                exit_code=0,
                stdout="",
                stderr="",
                error_message="",
            )
        )
        deleted = persistence.delete_old_logs(days=30)
        assert deleted == 1
        remaining = persistence.get_logs(job_id="jold")
        assert len(remaining) == 1
        assert remaining[0].log_id == "new1"

    def test_delete_job_cascades_logs(self, persistence):
        persistence.save_job(
            JobRecord(
                job_id="jc",
                name="cascade",
                command="echo",
                job_type="cron",
                schedule_expr="* * * * *",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        )
        persistence.save_log(
            LogRecord(
                log_id="c1",
                job_id="jc",
                started_at="2024-01-01T00:00:00",
                status="success",
                exit_code=0,
                stdout="",
                stderr="",
                error_message="",
            )
        )
        persistence.delete_job("jc")
        logs = persistence.get_logs(job_id="jc")
        assert len(logs) == 0
