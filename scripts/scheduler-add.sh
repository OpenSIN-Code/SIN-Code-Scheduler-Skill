#!/usr/bin/env bash
# Purpose: Add a job to the SIN-Scheduler via CLI.
# Docs: scripts/scheduler-add.sh.doc.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME=""
COMMAND=""
TYPE=""
EXPR=""
TIMEOUT=60
ENABLED=1

usage() {
    echo "Usage: $0 -n <name> -c <command> -t <cron|interval> -e <expr> [-o <timeout>] [-d]"
    echo "  -n  Job name"
    echo "  -c  Command to execute"
    echo "  -t  Schedule type: cron or interval"
    echo "  -e  Schedule expression (cron string or interval like 10m)"
    echo "  -o  Timeout seconds (default: 60)"
    echo "  -d  Disable job (default: enabled)"
    exit 1
}

while getopts ":n:c:t:e:o:d" opt; do
    case $opt in
        n) NAME="$OPTARG" ;;
        c) COMMAND="$OPTARG" ;;
        t) TYPE="$OPTARG" ;;
        e) EXPR="$OPTARG" ;;
        o) TIMEOUT="$OPTARG" ;;
        d) ENABLED=0 ;;
        *) usage ;;
    esac
done

if [ -z "$NAME" ] || [ -z "$COMMAND" ] || [ -z "$TYPE" ] || [ -z "$EXPR" ]; then
    usage
fi

python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/../src')
from sin_scheduler.scheduler import Scheduler
from sin_scheduler.persistence import Persistence
from sin_scheduler.jobs import Job
from pathlib import Path

p = Persistence(Path.home() / '.sin_scheduler' / 'scheduler.db')
s = Scheduler(persistence=p)

job = Job(
    name='$NAME',
    command='$COMMAND',
    job_type='$TYPE',
    schedule_expr='$EXPR',
    timeout_seconds=$TIMEOUT,
    enabled=bool($ENABLED),
)
job_id = s.add_job(job)
print(f'Added job {job_id}')
"
