from datetime import UTC, datetime

from canarias_lakehouse.ingestion.audit import COLUMNS, SCHEMA_DDL, AuditRecord, create_table_statement


def make_record(**overrides):
    values = {
        "run_id": "123",
        "environment": "dev",
        "dataset_name": "ds",
        "source_endpoint": "https://datos.canarias.es/api/x",
        "target_path": "/Volumes/c/s/v/ds/extraction_date=2026-10-25/run_ts=20261025T093005Z",
        "status": "SUCCEEDED",
        "started_at": datetime(2026, 10, 25, 9, 30, 5, tzinfo=UTC),
        "finished_at": datetime(2026, 10, 25, 9, 30, 35, tzinfo=UTC),
        "pages": 5,
        "records": 402,
        "bytes": 123456,
        "error_message": None,
    }
    return AuditRecord(**{**values, **overrides})


def test_row_matches_the_table_columns():
    row = make_record().as_row()

    assert len(row) == len(COLUMNS)
    assert row[COLUMNS.index(("duration_seconds", "DOUBLE", "Run duration in seconds"))] == 30.0


def test_schema_ddl_lists_columns_in_order():
    assert SCHEMA_DDL.startswith("run_id STRING, environment STRING, dataset_name STRING")
    assert SCHEMA_DDL.endswith("error_message STRING")


def test_create_table_statement_has_every_column_with_a_comment():
    sql = create_table_statement("workspace.ops.ingestion_audit")

    assert sql.startswith("CREATE TABLE IF NOT EXISTS workspace.ops.ingestion_audit (")
    for name, data_type, comment in COLUMNS:
        assert f"{name} {data_type} COMMENT '{comment}'" in sql
    assert all("'" not in comment for _, _, comment in COLUMNS)
