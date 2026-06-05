#!/usr/bin/env bash
# Purpose: Show the SIN-Scheduler daemon status.
# Docs: scripts/scheduler-status.sh.doc.md

set -euo pipefail

PID_FILE="${HOME}/.sin_scheduler/scheduler.pid"
LOG_FILE="${HOME}/.sin_scheduler/scheduler.log"
DB_FILE="${HOME}/.sin_scheduler/scheduler.db"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Scheduler: RUNNING (PID: $PID)"
        echo "Log file: $LOG_FILE"
        echo "Database: $DB_FILE"
        if [ -f "$LOG_FILE" ]; then
            echo "--- Last 5 log lines ---"
            tail -n 5 "$LOG_FILE" || true
        fi
    else
        echo "Scheduler: NOT RUNNING (stale PID file)"
    fi
else
    echo "Scheduler: NOT RUNNING"
fi
