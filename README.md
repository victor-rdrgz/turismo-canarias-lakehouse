# Canarias Lakehouse

Databricks lakehouse for Canary Islands public data, built to analyse how tourism pressures energy and housing.
Everything is defined as code and deployed with Declarative Automation Bundles (Databricks Asset Bundles).

## Architecture

```
Gobierno de Canarias APIs ──► landing (UC volume, raw NDJSON) ──► bronze ──► silver ──► gold
        (ISTAC)                     │
                                    └──► ops.ingestion_audit (one row per run)
```

- **Landing**: raw responses, immutable, one folder per run. Pattern in
  [ADR 0001](docs/adr/0001-landing-ingestion-pattern.md).
- **Audit**: every run, successful or failed, appends a row to `ops.ingestion_audit`.
- **Compute**: serverless. **Catalog**: Unity Catalog, schemas `landing` and `ops`.

## Repository layout

```
databricks.yml                     bundle: variables and targets (dev, staging, prod)
resources/
  unity_catalog.yml                schemas landing and ops, landing volume
  ingest_gobierno_canarias.job.yml job that ingests every endpoint in parallel
  ingestion_alerts.yml             data alerts on the audit table (prod)
src/
  canarias_lakehouse/ingestion/    ingestion logic (config, HTTP, landing, audit, runner)
  notebooks/                       thin notebook entry points used by jobs
tests/
  unit/                            unit tests (pytest, no network)
  integration/                     tests against a deployed target, run by CD on staging
docs/
  adr/                             architecture decision records (template: 0000-template.md)
  runbook.md                       response to each alert
  data-contracts/                  ODCS data contracts per source
.github/
  workflows/ci.yml                 lint, unit tests and bundle validation on every pull request
  workflows/cd.yml                 deployment: staging on merge to main, prod on release tag
  dependabot.yml                   weekly updates of GitHub Actions and Python dependencies
  pull_request_template.md         Definition of Done checklist
  ISSUE_TEMPLATE/                  issue forms: bug, feature, design question
  release.yml                      release notes categories, by pull request label
CONTRIBUTING.md                    way of working: issues, branches, pull requests, releases
CODE_OF_CONDUCT.md, SECURITY.md    community standards and vulnerability reporting
```

## Development

Requirements: Python 3.11, [uv](https://docs.astral.sh/uv/), Databricks CLI ≥ 1.22.1 authenticated to the workspace.

```bash
uv sync                            # install dependencies
uv run ruff check .                # lint
uv run ruff format --check .       # formatting
uv run pytest                      # unit tests
databricks bundle validate -t dev  # validate the bundle
databricks bundle deploy -t dev    # deploy to the development target
databricks bundle run ingest_gobierno_canarias_landing -t dev
```

## Environments

| Target | Deployed by | Identity | Objects | Schedule |
|---|---|---|---|---|
| `dev` | each developer, from their machine | developer | prefixed `dev_<user>_` | paused |
| `staging` | CD, on every merge to `main`; the job run is the integration test | service principal | prefixed `staging_` | paused |
| `prod` | CD, on a release tag, after approval | service principal | no prefix | active |

The three targets share the single Free Edition workspace and are isolated by name prefixes. CD authenticates as the
service principal with OAuth machine-to-machine credentials; workload identity federation needs the account
console, which Free Edition does not provide.

Work is planned in GitHub Issues. Branching, pull requests, the Definition of Done and releases are described in
[CONTRIBUTING.md](CONTRIBUTING.md); releases and their notes are in GitHub Releases.

## Data sources

| Dataset | Source | Endpoint |
|---|---|---|
| `istac_frontur_turistas` | ISTAC | `statistical-resources/v1.0/datasets/ISTAC/E16028B_000011` |
| `istac_vivienda_vacacional` | ISTAC | `statistical-resources/v1.0/datasets/ISTAC/C00065A_000061` |
| `istac_pasajeros_aeropuertos` | ISTAC | `statistical-resources/v1.0/datasets/ISTAC/C00017A_000001` |
| `istac_indicadores_catalogo` | ISTAC | `indicators/v1.0/indicators` (paginated) |

Data: © Instituto Canario de Estadística (ISTAC), reused under its legal notice.
