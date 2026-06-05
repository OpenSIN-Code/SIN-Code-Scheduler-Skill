#!/usr/bin/env bash
# Purpose: Stop the SIN-Scheduler daemon.
# Docs: scripts/scheduler-stop.sh.doc.md

set -euo pipefail

PID_FILE="${HOME}/.sin_scheduler/scheduler.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Scheduler not running (no PID file)"
    exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || true)
if [ -z "$PID" ]; then
    echo "Scheduler not running (empty PID file)"
    rm -f "$PID_FILE"
    exit 0
fi

if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping scheduler (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    sleep 1
    if kill -0 "$PID" 2>/dev/null; then
        echo "Force killing scheduler..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    echo "Scheduler stopped"
else
    echo "Scheduler not running (stale PID file)"
fi

rm -f "$PID_FILE"
