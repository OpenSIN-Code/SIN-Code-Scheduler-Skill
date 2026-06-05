#!/usr/bin/env bash
# Purpose: Remove a job from the SIN-Scheduler via CLI.
# Docs: scripts/scheduler-remove.sh.doc.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <job_id>"
    exit 1
fi

JOB_ID="$1"

python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/../src')
from sin_scheduler.scheduler import Scheduler
from sin_scheduler.persistence import Persistence
from pathlib import Path

p = Persistence(Path.home() / '.sin_scheduler' / 'scheduler.db')
s = Scheduler(persistence=p)

removed = s.remove_job('${JOB_ID}')
if removed:
    print(f'Removed job {JOB_ID}')
else:
    print(f'Job {JOB_ID} not found')
    sys.exit(1)
"
