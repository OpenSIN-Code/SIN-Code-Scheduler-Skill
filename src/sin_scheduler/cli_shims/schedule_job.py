# Purpose: CLI shim for schedule_job
# Docs: schedule_job.doc.md
"""CLI: schedule-job — schedule a new cron or interval job.

Usage: schedule-job <name> <command> <schedule-type> <schedule-expr>
                    [--timeout N] [--disabled] [--metadata JSON]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_job


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-job")
    parser.add_argument("name")
    parser.add_argument("command")
    parser.add_argument("schedule_type", choices=["cron", "interval"])
    parser.add_argument("schedule_expr", help="Cron string (e.g. '0 9 * * *') or interval (e.g. '10m')")
    parser.add_argument("--timeout", type=int, default=60, dest="timeout_seconds")
    parser.add_argument("--disabled", dest="enabled", action="store_false")
    parser.add_argument("--metadata", default="{}")
    args = parser.parse_args(argv)
    print(schedule_job(
        name=args.name,
        command=args.command,
        schedule_type=args.schedule_type,
        schedule_expr=args.schedule_expr,
        timeout_seconds=args.timeout_seconds,
        enabled=args.enabled,
        metadata=args.metadata,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
