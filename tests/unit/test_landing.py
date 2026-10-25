import json
from datetime import UTC, datetime

from canarias_lakehouse.ingestion.http_source import Page
from canarias_lakehouse.ingestion.landing import run_folder, with_metadata, write_page


def test_run_folder_is_partitioned_by_extraction_date_and_run_timestamp():
    started_at = datetime(2026, 10, 25, 9, 30, 5, tzinfo=UTC)

    folder = run_folder("/Volumes/workspace/landing/gobierno_canarias", "istac_frontur_turistas", started_at)

    assert folder == (
        "/Volumes/workspace/landing/gobierno_canarias/istac_frontur_turistas/"
        "extraction_date=2026-10-25/run_ts=20261025T093005Z"
    )


def test_metadata_is_added_without_changing_the_source_record():
    record = {"id": "PARO_REGISTRADO", "version": "1.4"}

    row = with_metadata(record, extracted_at="2026-10-25T09:30:05Z", dataset_name="ds", source_url="u", page=2)

    assert row == {
        "id": "PARO_REGISTRADO",
        "version": "1.4",
        "_extracted_at": "2026-10-25T09:30:05Z",
        "_dataset_name": "ds",
        "_source_url": "u",
        "_page": 2,
    }
    assert record == {"id": "PARO_REGISTRADO", "version": "1.4"}


def test_non_object_records_are_wrapped():
    row = with_metadata(42, extracted_at="t", dataset_name="ds", source_url="u", page=1)

    assert row["value"] == 42


def test_write_page_produces_one_json_object_per_line(tmp_path):
    page = Page(number=3, url="https://datos.canarias.es/api/x?offset=200", records=[{"id": "A"}, {"id": "Ñ"}])

    path = write_page(str(tmp_path), page, extracted_at="t", dataset_name="ds")

    assert path.endswith("part-00003.ndjson")
    lines = (tmp_path / "part-00003.ndjson").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["A", "Ñ"]
    assert all(json.loads(line)["_page"] == 3 for line in lines)
