# Project journal

Working log for the Canarias lakehouse. Newest entries at the bottom of the log.
Tasks will move to GitHub Issues once the repository is on GitHub.

## Approach

- One source at a time, end to end (access check, landing, bronze, silver, gold, quality checks, tests).
- Source order follows the `Prioridad` column of the source catalogue (kept outside the repository).
- Every source starts with an access check from Databricks Free Edition, because outbound internet is limited to a set of trusted domains.
- Everything that can be defined as code lives in the Databricks Asset Bundle; the web UI is only for exploring and debugging.
- Each design decision is recorded as an ADR in `docs/adr/`.

## Backlog (priority order)

| # | ID | Source | Mode | Status |
|---|----|--------|------|--------|
| 1 | T01 | ISTAC FRONTUR-Canarias (tourists by island, monthly) | Batch | Next: access check |
| 2 | T02 | ISTAC tourist accommodation | Batch | Pending |
| 3 | T03 | ISTAC holiday rentals | Batch | Pending |
| 4 | E01 | REE electricity demand (Canary system) | Batch | Pending |
| 5 | E03 | OMIE day-ahead prices | Batch | Pending |
| 6 | E04 | ISTAC available electricity by island | Batch | Pending |
| 7 | C03 | TITSA GTFS (Tenerife buses) | Batch | Pending |
| 8 | C08 | SITCAN weather observations | Batch | Pending |
| 9 | C21 | Canary Islands CKAN catalogue | Batch | Pending |
| 10 | V05 | ISTAC indicators | Batch | Pending |

## Log

### 2026-10-23

Done:
- Local tooling checked and authenticated: Python 3.11, Git, GitHub CLI, Databricks CLI.
- Python project initialised with uv; ruff and pytest added as dev dependencies.
- Repository initialised on `main`; first commits made with the GitHub no-reply address.
- `.gitignore` extended (secrets, local state, tool caches).
- Workspace explored: catalogs `system`, `samples`, `workspace`; schemas `default`, `information_schema`.
- Source catalogue built: 163 candidate sources, verified with real requests where possible.

Learned:
- Unity Catalog addresses data as `catalog.schema.object`; every catalog has a read-only `information_schema` with metadata views.
- Free Edition is serverless-only and restricts outbound internet to a limited set of trusted domains.
- Auto Loader reads from storage (Volumes), not directly over HTTP: files must be downloaded by a job first.

Next:
- Access check from Databricks serverless to the ISTAC domain (source T01).
