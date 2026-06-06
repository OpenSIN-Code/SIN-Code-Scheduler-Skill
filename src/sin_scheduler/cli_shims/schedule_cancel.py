# Purpose: CLI shim for schedule_cancel
# Docs: schedule_cancel.doc.md
"""CLI: schedule-cancel — cancel and remove a scheduled job.

Usage: schedule-cancel <job-id>
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_cancel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-cancel")
    parser.add_argument("job_id")
    args = parser.parse_args(argv)
    print(schedule_cancel(args.job_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
