# Purpose: CLI shim for schedule_list
# Docs: schedule_list.doc.md
"""CLI: schedule-list — list all scheduled jobs.

Usage: schedule-list [--enabled-only]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import schedule_list


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-list")
    parser.add_argument("--enabled-only", action="store_true")
    args = parser.parse_args(argv)
    print(schedule_list(enabled_only=args.enabled_only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
