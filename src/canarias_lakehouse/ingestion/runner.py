"""Runs one landing ingestion and always returns its audit record, also when it fails."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import requests

from canarias_lakehouse.ingestion.audit import AuditRecord
from canarias_lakehouse.ingestion.config import IngestionConfig
from canarias_lakehouse.ingestion.http_source import BASE_URL, build_session, iter_pages
from canarias_lakehouse.ingestion.landing import file_size, run_folder, write_page

log = logging.getLogger(__name__)


@dataclass
class IngestionOutcome:
    audit: AuditRecord
    files: list[str] = field(default_factory=list)
    error: Exception | None = None

    def summary(self) -> dict:
        return {
            "dataset_name": self.audit.dataset_name,
            "status": self.audit.status,
            "target_path": self.audit.target_path,
            "pages": self.audit.pages,
            "records": self.audit.records,
            "bytes": self.audit.bytes,
            "files": [os.path.basename(path) for path in self.files],
        }


def run_ingestion(
    config: IngestionConfig,
    *,
    session: requests.Session | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
) -> IngestionOutcome:
    """Extract every page into a new run folder. Errors are captured in the outcome, never swallowed silently."""
    started_at = now()
    folder = run_folder(config.target_volume_path, config.dataset_name, started_at)
    extracted_at = started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    files: list[str] = []
    pages = records = size = 0
    error: Exception | None = None

    try:
        if not os.path.isdir(config.target_volume_path):
            raise FileNotFoundError(f"Volume not found or not accessible: {config.target_volume_path}")
        os.makedirs(folder, exist_ok=False)
        for page in iter_pages(session or build_session(), config.endpoint_path, config.pagination, sleep=sleep):
            path = write_page(folder, page, extracted_at=extracted_at, dataset_name=config.dataset_name)
            files.append(path)
            pages += 1
            records += len(page.records)
            size += file_size(path)
            log.info("page=%s records=%s file=%s", page.number, len(page.records), path)
    except Exception as exc:  # recorded as FAILED in the audit row; the caller re-raises
        log.exception("Ingestion of %s failed", config.dataset_name)
        error = exc

    audit = AuditRecord(
        run_id=config.job_run_id or None,
        environment=config.environment or None,
        dataset_name=config.dataset_name,
        source_endpoint=f"{BASE_URL}{config.endpoint_path}",
        target_path=folder,
        status="FAILED" if error else "SUCCEEDED",
        started_at=started_at,
        finished_at=now(),
        pages=pages,
        records=records,
        bytes=size,
        error_message=f"{type(error).__name__}: {error}"[:4000] if error else None,
    )
    return IngestionOutcome(audit=audit, files=files, error=error)
