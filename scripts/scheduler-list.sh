#!/usr/bin/env bash
# Purpose: List all jobs in the SIN-Scheduler via CLI.
# Docs: scheduler-list.sh.doc.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/../src')
from sin_scheduler.scheduler import Scheduler
from sin_scheduler.persistence import Persistence
from pathlib import Path

p = Persistence(Path.home() / '.sin_scheduler' / 'scheduler.db')
s = Scheduler(persistence=p)

jobs = s.list_jobs()
if not jobs:
    print('No jobs scheduled')
    sys.exit(0)

for j in jobs:
    status = 'enabled' if j.enabled else 'disabled'
    print(f'{j.job_id} | {j.name} | {j.job_type} | {j.schedule_expr} | {status} | runs={j.run_count} | fails={j.failure_count}')
"
