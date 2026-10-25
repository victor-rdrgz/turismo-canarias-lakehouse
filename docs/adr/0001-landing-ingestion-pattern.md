# ADR 0001: Landing ingestion pattern

- Status: Accepted
- Date: 2026-10-25

## Context

The project ingests many public HTTP APIs (first provider: Gobierno de Canarias, ISTAC). Raw data must land in
Databricks before any transformation, in a way that is reproducible, auditable and safe to re-run. Each run needs
an operational record that can be queried, alerted on and reconciled against the source.

## Decision

Every ingestion into the landing zone follows this pattern:

1. **Landing storage.** Raw files are written to a Unity Catalog managed volume in the `landing` schema, one volume
   per provider and one folder per dataset.
2. **Immutable run folders.** Each run writes to a new folder
   `<dataset>/extraction_date=YYYY-MM-DD/run_ts=YYYYMMDDTHHMMSSZ/`. Files are never overwritten or modified.
3. **Format.** Data files are NDJSON (one JSON object per line), one file per API page, named `part-NNNNN.ndjson`.
   Each record keeps the source payload unchanged and adds extraction metadata columns: `_extracted_at`,
   `_dataset_name`, `_source_url`, `_page`.
4. **Resilient HTTP.** Requests use exponential backoff on timeouts, connection errors, HTTP 429 and 5xx, and respect
   the `Retry-After` header.
5. **Audit table.** Every run, successful or failed, appends one row to a Delta audit table in Unity Catalog with:
   run id, dataset, source endpoint, target path, status, start and end timestamps, duration, pages, records, bytes
   and error message. The job run id is passed to the task as the `{{job.run_id}}` dynamic value reference.
6. **No marker files.** No `_SUCCESS` or similar files are written to landing.

## Consequences

- Any run can be traced from a landing folder to its audit row and job run, and back.
- Failed and partial runs are visible with SQL; downstream steps and alerts can rely on the audit table.
- Re-running is safe: it creates a new run folder; deduplication across runs happens downstream.
- Readers of landing only see data files, so nothing has to be filtered out.
- The audit table lives in a separate operations schema and must exist per environment (dev and prod).

## Alternatives considered

- **`_SUCCESS` marker file per run folder.** Rejected: it duplicates the run summary, cannot be queried with SQL,
  and Auto Loader cannot use it to skip incomplete runs.
- **Overwriting a single "latest" file per dataset.** Rejected: loses history and makes reprocessing impossible.
