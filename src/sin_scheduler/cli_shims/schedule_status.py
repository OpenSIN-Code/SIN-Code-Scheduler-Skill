# Purpose: CLI shim for schedule_status
# Docs: schedule_status.doc.md
"""CLI: schedule-status — show job status.

Usage: schedule-status <job-id>
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-status")
    parser.add_argument("job_id")
    args = parser.parse_args(argv)
    print(schedule_status(args.job_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
