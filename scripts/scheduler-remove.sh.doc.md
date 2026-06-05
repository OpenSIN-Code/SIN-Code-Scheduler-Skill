# `scripts/scheduler-remove.sh`

## What it does
Removes a scheduled job by its ID.

## Dependencies
- `python3` with `sin_scheduler` on `PYTHONPATH`

## Usage
```bash
./scripts/scheduler-remove.sh <job_id>
```

## Notes
- Exits with code 1 if the job is not found.
- Deletes the job and all its logs from the database.
