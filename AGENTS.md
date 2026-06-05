# SIN-Code-Scheduler-Skill — Agent Instructions

## ⚠️ GitNexus-Pflicht

Bevor du Code in diesem Repo änderst, MUSST du:
- `gitnexus_impact()` — Blast Radius prüfen
- `gitnexus_detect_changes()` — Vor jedem Commit

## Tools

- `sin-scheduler-mcp` — FastMCP server (stdio transport)
- `scripts/scheduler-*.sh` — CLI wrapper

## CoDocs

Jede `.py` Datei hat eine `.doc.md` Partner-Datei im selben Verzeichnis.

## Commits

- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`)
- Direkt auf `main` — keine Branches

## Testing

```bash
pytest -q
```

Alle Tests müssen grün sein vor dem Push.

## Database

- `~/.sin_scheduler/scheduler.db` — SQLite, nicht im Repo
- `SIN_SCHEDULER_DB` Env-Var überschreibt den Pfad

## CI

- `ceo-audit.yml` läuft bei jedem Push
- Grade gate: B
