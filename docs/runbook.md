# Runbook: landing ingestion

How to respond to every alert of the `ingest_gobierno_canarias_landing` job in `prod`. All alerts are emailed to
the `alert_email` bundle variable.

## Where to look

- **Job runs**: Jobs & Pipelines → `ingest_gobierno_canarias_landing` → run → failed task → output and logs.
- **Audit table**: `workspace.ops.ingestion_audit`, one row per run (ADR 0001).

  ```sql
  SELECT dataset_name, status, started_at, records, error_message, target_path
  FROM workspace.ops.ingestion_audit
  ORDER BY started_at DESC
  LIMIT 20;
  ```

- **Landing files**: the run folder in `target_path`.
- **Job history**: `system.lakeflow.job_run_timeline` and `system.lakeflow.job_task_run_timeline`.

## Alerts

### Job failure

The job failed after the last task retry: one or more datasets have a `FAILED` audit row.

1. Read `error_message` in the audit table and the failed task output.
2. By cause:
   - **HTTP 429 or 5xx after every retry**: the source is down or rate limiting. Check the endpoint in a browser or a
     notebook; if the source is down, wait for the next scheduled run.
   - **HTTP 4xx (except 429)**: the endpoint changed. Compare with the data contract in `docs/data-contracts/`,
     open a bug and fix the endpoint in the job definition.
   - **Volume or permission errors**: check that the identity running the job (the service principal) still has
     access to the catalog, schemas and volume.
   - **Audit table errors**: the run's data was written but its audit row was not; open a bug with the run id.
3. Re-run the failed tasks from the job run page (Repair run). A repair writes new run folders; landing is never
   edited by hand.

### Duration warning

The run has been going for over 1 hour; it is cancelled at 2 hours.

1. Find the running task and the page it is requesting in its logs.
2. Slow source responses are retried with backoff; if the source is degraded, let the timeout cancel the run and
   rely on the next scheduled run, or cancel it.

### Stale datasets (`[landing] Stale datasets`)

A dataset has no successful ingestion in the last 26 hours.

1. Check that the job schedule is active and that the last scheduled run started.
2. If runs failed, follow **Job failure**. If no run started, check the workspace quota: Free Edition shuts down
   compute for the rest of the day when the daily quota is exceeded.

### Low record counts (`[landing] Low record counts`)

The latest successful run of a dataset wrote no records, or fewer than half of its average over the previous seven
successful runs.

1. Open the run folder and the source endpoint, and compare with the data contract.
2. A legitimate drop (a smaller source publication) needs no action; a schema or endpoint change is a bug.

### Alert in error state

An alert query failed, for example because the audit table does not exist yet or the warehouse is unavailable. Check
the alert's query history in Databricks SQL.
