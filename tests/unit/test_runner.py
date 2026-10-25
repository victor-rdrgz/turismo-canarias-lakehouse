import json
import os
from datetime import UTC, datetime

import requests

from canarias_lakehouse.ingestion.config import IngestionConfig
from canarias_lakehouse.ingestion.runner import run_ingestion

from .fakes import FakeResponse, FakeSession

START = datetime(2026, 10, 25, 9, 30, 5, tzinfo=UTC)
END = datetime(2026, 10, 25, 9, 30, 20, tzinfo=UTC)


def clock():
    times = iter([START, END])
    return lambda: next(times)


def config_for(volume_path, pagination="offset"):
    return IngestionConfig(
        endpoint_path="/api/estadisticas/indicators/v1.0/indicators",
        dataset_name="istac_indicadores_catalogo",
        target_volume_path=volume_path,
        audit_table="workspace.ops.ingestion_audit",
        environment="dev",
        job_run_id="987",
        pagination=pagination,
    )


def test_successful_run_writes_pages_and_a_succeeded_audit_record(tmp_path):
    session = FakeSession(
        [
            {"total": 150, "items": [{"id": i} for i in range(100)]},
            {"total": 150, "items": [{"id": i} for i in range(100, 150)]},
        ]
    )

    outcome = run_ingestion(config_for(str(tmp_path)), session=session, now=clock(), sleep=lambda _: None)

    assert outcome.error is None
    audit = outcome.audit
    assert (audit.status, audit.pages, audit.records) == ("SUCCEEDED", 2, 150)
    assert audit.bytes == sum(os.path.getsize(f) for f in outcome.files)
    assert audit.run_id == "987" and audit.environment == "dev"
    assert audit.duration_seconds == 15.0
    assert audit.target_path.endswith("istac_indicadores_catalogo/extraction_date=2026-10-25/run_ts=20261025T093005Z")
    with open(outcome.files[0], encoding="utf-8") as part:
        first_line = part.readline()
    assert json.loads(first_line)["_extracted_at"] == "2026-10-25T09:30:05Z"


def test_missing_volume_is_audited_as_failed(tmp_path):
    outcome = run_ingestion(config_for(str(tmp_path / "missing")), session=FakeSession([]), now=clock())

    assert isinstance(outcome.error, FileNotFoundError)
    assert outcome.audit.status == "FAILED"
    assert outcome.audit.error_message.startswith("FileNotFoundError")
    assert outcome.audit.pages == 0


def test_failure_midway_keeps_what_was_written_in_the_audit_record(tmp_path):
    session = FakeSession(
        [
            {"total": 300, "items": [{"id": i} for i in range(100)]},
            FakeResponse({}, "https://datos.canarias.es/api/x?offset=100", status_code=503),
        ]
    )

    outcome = run_ingestion(config_for(str(tmp_path)), session=session, now=clock(), sleep=lambda _: None)

    assert isinstance(outcome.error, requests.HTTPError)
    assert (outcome.audit.status, outcome.audit.pages, outcome.audit.records) == ("FAILED", 1, 100)


def test_run_without_job_context_has_no_run_id(tmp_path):
    config = IngestionConfig(**{**config_for(str(tmp_path)).__dict__, "job_run_id": "", "pagination": "none"})

    outcome = run_ingestion(config, session=FakeSession([{"id": "cube"}]), now=clock())

    assert outcome.audit.run_id is None
    assert outcome.audit.records == 1
