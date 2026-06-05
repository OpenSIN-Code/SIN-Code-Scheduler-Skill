#!/usr/bin/env bash
# Purpose: Start the SIN-Scheduler daemon.
# Docs: scripts/scheduler-start.sh.doc.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${HOME}/.sin_scheduler/scheduler.pid"
LOG_FILE="${HOME}/.sin_scheduler/scheduler.log"
DB_DIR="${HOME}/.sin_scheduler"

mkdir -p "$DB_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Scheduler already running (PID: $PID)"
        exit 0
    fi
fi

echo "Starting SIN-Scheduler daemon..."

# Run the scheduler in background via Python
nohup python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/../src')
from sin_scheduler.scheduler import Scheduler
from sin_scheduler.persistence import Persistence
from pathlib import Path
p = Persistence(Path('${DB_DIR}/scheduler.db'))
s = Scheduler(persistence=p)
s.start()
print('Scheduler started', flush=True)
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    s.stop()
" > "$LOG_FILE" 2>&1 &

PID=$!
echo "$PID" > "$PID_FILE"
echo "Scheduler started (PID: $PID, log: $LOG_FILE)"
