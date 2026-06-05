# `tests/test_jobs.py`

## What it does
Tests the `Job` dataclass and `JobType` enum covering:
- Default construction and explicit field assignment
- UUID generation
- Serialization roundtrip (`to_record` / `from_record`)
- `bump_run()` side effects
- Enum values

## Test classes
- `TestJobCreation` — defaults and explicit values
- `TestJobSerialization` — record conversion and roundtrip
- `TestJobBumpRun` — counter and timestamp updates
- `TestJobTypeEnum` — enum value verification

## Notes
- `from_record` requires all fields present; used in production via `**record`.
- `bump_run` mutates the object in place.
