"""Integration test of a deployed ingestion job run, executed by CD against the staging target.

Required environment variables (set by the CD workflow):
- DATABRICKS_HOST and credentials of the deploying identity
- DATABRICKS_WAREHOUSE_ID: SQL warehouse used to query the audit table
- INTEGRATION_AUDIT_TABLE: <catalog>.<schema>.ingestion_audit of the target under test
- INTEGRATION_ENVIRONMENT: bundle target under test
- INTEGRATION_RUN_STARTED_AT: UTC timestamp taken just before the job run, as YYYY-MM-DD HH:MM:SS
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

JOB_FILE = Path(__file__).parents[2] / "resources" / "ingest_gobierno_canarias.job.yml"
JOB_KEY = "ingest_gobierno_canarias_landing"
STATEMENT_TIMEOUT_SECONDS = 600
SETTINGS = (
    "DATABRICKS_WAREHOUSE_ID",
    "INTEGRATION_AUDIT_TABLE",
    "INTEGRATION_ENVIRONMENT",
    "INTEGRATION_RUN_STARTED_AT",
)


def expected_datasets() -> set[str]:
    job = yaml.safe_load(JOB_FILE.read_text(encoding="utf-8"))["resources"]["jobs"][JOB_KEY]
    return {task["notebook_task"]["base_parameters"]["dataset_name"] for task in job["tasks"]}


def latest_audit_rows(audit_table: str, environment: str, started_at: str) -> dict[str, tuple[str, int]]:
    """Latest audit row per dataset written by the run under test: {dataset_name: (status, records)}."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.sql import StatementParameterListItem, StatementState

    client = WorkspaceClient()
    statement = f"""
        SELECT dataset_name, status, records
        FROM {audit_table}
        WHERE environment = :environment AND started_at >= :started_at
        QUALIFY row_number() OVER (PARTITION BY dataset_name ORDER BY started_at DESC) = 1
    """
    response = client.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=os.environ["DATABRICKS_WAREHOUSE_ID"],
        parameters=[
            StatementParameterListItem(name="environment", value=environment),
            StatementParameterListItem(name="started_at", value=started_at, type="TIMESTAMP"),
        ],
        wait_timeout="50s",
    )
    deadline = time.monotonic() + STATEMENT_TIMEOUT_SECONDS
    while response.status.state in (StatementState.PENDING, StatementState.RUNNING):
        if time.monotonic() > deadline:
            client.statement_execution.cancel_execution(response.statement_id)
            pytest.fail(f"Audit query did not finish in {STATEMENT_TIMEOUT_SECONDS} s")
        time.sleep(5)
        response = client.statement_execution.get_statement(response.statement_id)
    if response.status.state != StatementState.SUCCEEDED:
        pytest.fail(f"Audit query {response.status.state}: {response.status.error}")
    rows = response.result.data_array or []
    return {name: (status, int(records)) for name, status, records in rows}


@pytest.fixture(scope="module")
def run_settings() -> dict[str, str]:
    missing = [name for name in SETTINGS if not os.environ.get(name)]
    if missing:
        pytest.skip(f"Integration settings not set: {', '.join(missing)}")
    return {name: os.environ[name] for name in SETTINGS}


def test_every_dataset_of_the_job_run_succeeded_with_records(run_settings):
    rows = latest_audit_rows(
        run_settings["INTEGRATION_AUDIT_TABLE"],
        run_settings["INTEGRATION_ENVIRONMENT"],
        run_settings["INTEGRATION_RUN_STARTED_AT"],
    )

    assert set(rows) == expected_datasets()
    failed = {name: status for name, (status, _) in rows.items() if status != "SUCCEEDED"}
    assert not failed, f"Datasets not SUCCEEDED: {failed}"
    empty = [name for name, (_, records) in rows.items() if records == 0]
    assert not empty, f"Datasets with no records: {empty}"
