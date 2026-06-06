# Purpose: CLI shim for schedule_logs
# Docs: schedule_logs.doc.md
"""CLI: schedule-logs — show recent job execution logs.

Usage: schedule-logs [--job-id ID] [--limit N] [--status STATUS]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_logs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-logs")
    parser.add_argument("--job-id", dest="job_id", default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--status", default="", choices=["", "pending", "running", "success", "failed", "timeout"]
    )
    args = parser.parse_args(argv)
    print(schedule_logs(job_id=args.job_id, limit=args.limit, status=args.status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
