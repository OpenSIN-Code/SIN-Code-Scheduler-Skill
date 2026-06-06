# Purpose: CLI shim for schedule_run_now
# Docs: schedule_run_now.doc.md
"""CLI: schedule-run-now — trigger a job immediately.

Usage: schedule-run-now <job-id>
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_run_now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-run-now")
    parser.add_argument("job_id")
    args = parser.parse_args(argv)
    print(schedule_run_now(args.job_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
