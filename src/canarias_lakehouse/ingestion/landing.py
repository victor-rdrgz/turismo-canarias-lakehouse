"""Landing volume layout: one immutable folder per run, one NDJSON file per page."""

from __future__ import annotations

import json
import os
import posixpath
from datetime import datetime
from typing import Any

from canarias_lakehouse.ingestion.http_source import Page


def run_folder(volume_path: str, dataset_name: str, started_at: datetime) -> str:
    """<volume>/<dataset>/extraction_date=YYYY-MM-DD/run_ts=YYYYMMDDTHHMMSSZ (UTC)."""
    return posixpath.join(
        volume_path,
        dataset_name,
        f"extraction_date={started_at:%Y-%m-%d}",
        f"run_ts={started_at:%Y%m%dT%H%M%SZ}",
    )


def with_metadata(record: Any, *, extracted_at: str, dataset_name: str, source_url: str, page: int) -> dict:
    """Source record unchanged plus extraction metadata; non-object records are wrapped under 'value'."""
    row = dict(record) if isinstance(record, dict) else {"value": record}
    row.update(
        {
            "_extracted_at": extracted_at,
            "_dataset_name": dataset_name,
            "_source_url": source_url,
            "_page": page,
        }
    )
    return row


def write_page(folder: str, page: Page, *, extracted_at: str, dataset_name: str) -> str:
    """Write a page as part-NNNNN.ndjson in one sequential write (volumes support no appends)."""
    path = posixpath.join(folder, f"part-{page.number:05d}.ndjson")
    with open(path, "w", encoding="utf-8") as fh:
        for record in page.records:
            row = with_metadata(
                record, extracted_at=extracted_at, dataset_name=dataset_name, source_url=page.url, page=page.number
            )
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path


def file_size(path: str) -> int:
    return os.path.getsize(path)
