"""
Purpose: Test the Scheduler (cron, interval, lifecycle, status).
Docs: tests/test_scheduler.doc.md
"""
import time
from pathlib import Path

import pytest

from sin_scheduler.executor import Executor
from sin_scheduler.jobs import Job
from sin_scheduler.persistence import Persistence
from sin_scheduler.scheduler import Scheduler


@pytest.fixture
def temp_db(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def scheduler(temp_db):
    p = Persistence(db_path=temp_db)
    s = Scheduler(persistence=p)
    yield s
    s.stop()


class TestSchedulerLifecycle:
    def test_start_stop(self, scheduler):
        assert not scheduler.is_running()
        scheduler.start()
        assert scheduler.is_running()
        scheduler.stop()
        assert not scheduler.is_running()

    def test_double_start(self, scheduler):
        scheduler.start()
        scheduler.start()  # should be no-op
        assert scheduler.is_running()

    def test_double_stop(self, scheduler):
        scheduler.stop()
        scheduler.stop()  # should be no-op
        assert not scheduler.is_running()

    def test_stop_after_start(self, scheduler):
        scheduler.start()
        time.sleep(0.2)
        scheduler.stop()
        assert not scheduler.is_running()


class TestSchedulerAddRemove:
    def test_add_cron_job(self, scheduler):
        job = Job(name="cron", command="echo hi", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        assert job_id == job.job_id
        fetched = scheduler.get_job(job_id)
        assert fetched is not None
        assert fetched.name == "cron"

    def test_add_interval_job(self, scheduler):
        job = Job(name="int", command="echo hi", job_type="interval", schedule_expr="10m")
        job_id = scheduler.add_job(job)
        fetched = scheduler.get_job(job_id)
        assert fetched is not None
        assert fetched.job_type == "interval"

    def test_add_disabled_job(self, scheduler):
        job = Job(name="off", command="echo hi", job_type="interval", schedule_expr="5m", enabled=False)
        job_id = scheduler.add_job(job)
        fetched = scheduler.get_job(job_id)
        assert fetched is not None
        assert fetched.enabled is False

    def test_remove_job(self, scheduler):
        job = Job(name="rem", command="echo hi", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        assert scheduler.remove_job(job_id) is True
        assert scheduler.get_job(job_id) is None

    def test_remove_nonexistent(self, scheduler):
        assert scheduler.remove_job("fake") is False

    def test_list_jobs(self, scheduler):
        for i in range(3):
            scheduler.add_job(
                Job(name=f"j{i}", command="echo", job_type="cron", schedule_expr="* * * * *", enabled=i < 2)
            )
        all_jobs = scheduler.list_jobs()
        assert len(all_jobs) == 3
        enabled = scheduler.list_jobs(enabled_only=True)
        assert len(enabled) == 2

    def test_get_job_not_found(self, scheduler):
        assert scheduler.get_job("nope") is None

    def test_add_job_persists(self, scheduler):
        job = Job(name="persist", command="echo", job_type="cron", schedule_expr="0 0 * * *")
        job_id = scheduler.add_job(job)
        # Create a new scheduler pointing to the same DB
        p2 = Persistence(db_path=scheduler.persistence.db_path)
        s2 = Scheduler(persistence=p2)
        fetched = s2.get_job(job_id)
        assert fetched is not None
        assert fetched.name == "persist"


class TestSchedulerIntervalParsing:
    def test_interval_seconds(self, scheduler):
        job = Job(name="s", command="echo", job_type="interval", schedule_expr="5s")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None

    def test_interval_minutes(self, scheduler):
        job = Job(name="m", command="echo", job_type="interval", schedule_expr="10m")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None

    def test_interval_hours(self, scheduler):
        job = Job(name="h", command="echo", job_type="interval", schedule_expr="2h")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None

    def test_interval_days(self, scheduler):
        job = Job(name="d", command="echo", job_type="interval", schedule_expr="1d")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None

    def test_interval_invalid_unit(self, scheduler):
        job = Job(name="bad", command="echo", job_type="interval", schedule_expr="10x")
        with pytest.raises(ValueError, match="Unknown interval unit"):
            scheduler.add_job(job)

    def test_interval_zero_value(self, scheduler):
        job = Job(name="zero", command="echo", job_type="interval", schedule_expr="0m")
        with pytest.raises(ValueError, match="Invalid interval value"):
            scheduler.add_job(job)

    def test_interval_empty(self, scheduler):
        job = Job(name="empty", command="echo", job_type="interval", schedule_expr="")
        with pytest.raises(ValueError, match="Empty interval expression"):
            scheduler.add_job(job)


class TestSchedulerCron:
    def test_cron_valid(self, scheduler):
        job = Job(name="cron", command="echo", job_type="cron", schedule_expr="0 9 * * *")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None

    def test_cron_complex(self, scheduler):
        job = Job(name="complex", command="echo", job_type="cron", schedule_expr="*/15 8-17 * * 1-5")
        scheduler.add_job(job)
        assert scheduler.get_job(job.job_id) is not None


class TestSchedulerRunNow:
    def test_run_now_success(self, scheduler):
        job = Job(name="run", command="echo success", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        result = scheduler.run_job_now(job_id)
        assert result.status == "success"
        assert "success" in result.stdout

    def test_run_now_failure(self, scheduler):
        job = Job(name="fail", command="exit 1", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        result = scheduler.run_job_now(job_id)
        assert result.status == "failed"

    def test_run_now_not_found(self, scheduler):
        with pytest.raises(ValueError, match="Job not found"):
            scheduler.run_job_now("fake")

    def test_run_now_updates_stats(self, scheduler):
        job = Job(name="stats", command="echo hi", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        scheduler.run_job_now(job_id)
        fetched = scheduler.get_job(job_id)
        assert fetched.run_count == 1
        assert fetched.last_run != ""

    def test_run_now_logs(self, scheduler):
        job = Job(name="log", command="echo hi", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        scheduler.run_job_now(job_id)
        logs = scheduler.get_logs(job_id=job_id)
        assert len(logs) >= 1


class TestSchedulerStatus:
    def test_status(self, scheduler):
        job = Job(name="st", command="echo", job_type="cron", schedule_expr="0 0 * * *")
        job_id = scheduler.add_job(job)
        status = scheduler.get_status(job_id)
        assert status["job_id"] == job_id
        assert status["name"] == "st"
        assert "recent_logs" in status

    def test_status_not_found(self, scheduler):
        with pytest.raises(ValueError, match="Job not found"):
            scheduler.get_status("fake")


class TestSchedulerEnableDisable:
    def test_disable_job(self, scheduler):
        job = Job(name="off", command="echo", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        assert scheduler.disable_job(job_id) is True
        fetched = scheduler.get_job(job_id)
        assert fetched.enabled is False

    def test_enable_job(self, scheduler):
        job = Job(name="on", command="echo", job_type="cron", schedule_expr="* * * * *", enabled=False)
        job_id = scheduler.add_job(job)
        assert scheduler.enable_job(job_id) is True
        fetched = scheduler.get_job(job_id)
        assert fetched.enabled is True

    def test_disable_nonexistent(self, scheduler):
        assert scheduler.disable_job("fake") is False

    def test_enable_nonexistent(self, scheduler):
        assert scheduler.enable_job("fake") is False


class TestSchedulerLogs:
    def test_get_logs_empty(self, scheduler):
        logs = scheduler.get_logs()
        assert logs == []

    def test_get_logs_by_status(self, scheduler):
        job = Job(name="log", command="exit 1", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        scheduler.run_job_now(job_id)
        logs = scheduler.get_logs(job_id=job_id, status="failed")
        assert len(logs) == 1

    def test_get_logs_limit(self, scheduler):
        job = Job(name="many", command="echo x", job_type="cron", schedule_expr="* * * * *")
        job_id = scheduler.add_job(job)
        for _ in range(5):
            scheduler.run_job_now(job_id)
        logs = scheduler.get_logs(job_id=job_id, limit=2)
        assert len(logs) == 2


class TestSchedulerPersistence:
    def test_persisted_across_instances(self, temp_db):
        p1 = Persistence(db_path=temp_db)
        s1 = Scheduler(persistence=p1)
        job = Job(name="persist", command="echo", job_type="cron", schedule_expr="0 0 * * *")
        job_id = s1.add_job(job)

        p2 = Persistence(db_path=temp_db)
        s2 = Scheduler(persistence=p2)
        fetched = s2.get_job(job_id)
        assert fetched is not None
        assert fetched.name == "persist"
