"""Ingestion audit table: one row per run, successful or failed (ADR 0001)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

TABLE_COMMENT = "Landing ingestion audit: one row per run, successful or failed (ADR 0001)"

COLUMNS = (
    ("run_id", "STRING", "Lakeflow job run id; null for manual runs"),
    ("environment", "STRING", "Bundle target that ran the ingestion (dev or prod)"),
    ("dataset_name", "STRING", "Dataset folder name in the landing volume"),
    ("source_endpoint", "STRING", "Source endpoint URL without pagination parameters"),
    ("target_path", "STRING", "Run folder in the landing volume"),
    ("status", "STRING", "SUCCEEDED or FAILED"),
    ("started_at", "TIMESTAMP", "Run start (UTC)"),
    ("finished_at", "TIMESTAMP", "Run end (UTC)"),
    ("duration_seconds", "DOUBLE", "Run duration in seconds"),
    ("pages", "INT", "Pages written to landing"),
    ("records", "BIGINT", "Records written to landing"),
    ("bytes", "BIGINT", "Bytes written to landing"),
    ("error_message", "STRING", "Error type and message when status is FAILED"),
)

SCHEMA_DDL = ", ".join(f"{name} {data_type}" for name, data_type, _ in COLUMNS)


def create_table_statement(table_name: str) -> str:
    """CREATE TABLE IF NOT EXISTS with explicit types and column comments."""
    columns = ",\n  ".join(f"{name} {data_type} COMMENT '{comment}'" for name, data_type, comment in COLUMNS)
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  {columns}\n)\nCOMMENT '{TABLE_COMMENT}'"


@dataclass(frozen=True)
class AuditRecord:
    run_id: str | None
    environment: str | None
    dataset_name: str
    source_endpoint: str
    target_path: str
    status: str
    started_at: datetime
    finished_at: datetime
    pages: int
    records: int
    bytes: int
    error_message: str | None

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    def as_row(self) -> tuple:
        """Values in the column order of COLUMNS."""
        return (
            self.run_id,
            self.environment,
            self.dataset_name,
            self.source_endpoint,
            self.target_path,
            self.status,
            self.started_at,
            self.finished_at,
            self.duration_seconds,
            self.pages,
            self.records,
            self.bytes,
            self.error_message,
        )
