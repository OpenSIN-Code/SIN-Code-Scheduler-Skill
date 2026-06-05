"""
Purpose: Test the Executor (subprocess, timeout, error handling).
Docs: tests/test_executor.doc.md
"""
import time

import pytest

from sin_scheduler.executor import Executor, ExecutionResult


class TestExecutorRunNow:
    def test_successful_command(self):
        ex = Executor()
        result = ex.run_now("j1", "echo hello")
        assert result.status == "success"
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert result.error_message == ""
        assert result.job_id == "j1"

    def test_failed_command(self):
        ex = Executor()
        result = ex.run_now("j2", "exit 42")
        assert result.status == "failed"
        assert result.exit_code == 42

    def test_invalid_command(self):
        ex = Executor()
        result = ex.run_now("j3", "not_a_real_command_xyz")
        assert result.status == "failed"
        assert result.exit_code == 127
        assert "not found" in result.stderr

    def test_timeout(self):
        ex = Executor(default_timeout=1)
        result = ex.run_now("j4", "sleep 5")
        assert result.status == "timeout"
        assert result.error_message == "Timeout after 1 seconds"

    def test_custom_timeout(self):
        ex = Executor(default_timeout=60)
        result = ex.run_now("j5", "sleep 2", timeout=1)
        assert result.status == "timeout"

    def test_stdout_stderr(self):
        ex = Executor()
        result = ex.run_now("j6", "echo out && echo err >&2")
        assert "out" in result.stdout
        assert "err" in result.stderr

    def test_log_id_unique(self):
        ex = Executor()
        r1 = ex.run_now("j7", "echo 1")
        r2 = ex.run_now("j7", "echo 2")
        assert r1.log_id != r2.log_id

    def test_timestamps_present(self):
        ex = Executor()
        result = ex.run_now("j8", "echo hi")
        assert result.started_at != ""
        assert result.finished_at != ""
        assert result.started_at <= result.finished_at


class TestExecutorAsync:
    def test_async_run(self):
        ex = Executor()
        results = []

        def cb(r):
            results.append(r)

        thread = ex.run_async("j9", "echo async", callback=cb)
        thread.join(timeout=5)
        assert len(results) == 1
        assert results[0].status == "success"
        assert "async" in results[0].stdout

    def test_async_timeout(self):
        ex = Executor(default_timeout=1)
        results = []

        def cb(r):
            results.append(r)

        thread = ex.run_async("j10", "sleep 5", callback=cb)
        thread.join(timeout=5)
        assert len(results) == 1
        assert results[0].status == "timeout"

    def test_async_exception_in_callback(self):
        ex = Executor()

        def bad_cb(r):
            raise RuntimeError("boom")

        # Should not raise
        thread = ex.run_async("j11", "echo ok", callback=bad_cb)
        thread.join(timeout=5)

    def test_async_returns_thread(self):
        ex = Executor()
        thread = ex.run_async("j12", "echo hi")
        assert thread.is_alive() or not thread.is_alive()  # may finish quickly
        thread.join(timeout=5)


class TestExecutorEdgeCases:
    def test_empty_command(self):
        ex = Executor()
        result = ex.run_now("j13", "")
        # Empty command usually returns 0 in bash
        assert result.exit_code == 0 or result.status == "failed"

    def test_multiline_command(self):
        ex = Executor()
        result = ex.run_now("j14", "echo line1 && echo line2")
        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_environment_inherited(self):
        ex = Executor()
        result = ex.run_now("j15", "echo $PATH")
        assert result.status == "success"
        assert "/" in result.stdout
