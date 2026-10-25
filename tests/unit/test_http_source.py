import pytest
import requests

from canarias_lakehouse.ingestion import http_source
from canarias_lakehouse.ingestion.http_source import build_session, iter_pages

from .fakes import FakeResponse, FakeSession


def items(n):
    return [{"id": f"IND_{i}"} for i in range(n)]


def test_no_pagination_returns_whole_response_as_one_record():
    session = FakeSession([{"id": "E16028B_000011", "data": {}}])

    pages = list(iter_pages(session, "/api/x/~latest.json", "none"))

    assert len(pages) == 1
    assert pages[0].records == [{"id": "E16028B_000011", "data": {}}]
    assert session.calls[0]["params"] is None
    assert session.calls[0]["url"] == "https://datos.canarias.es/api/x/~latest.json"


def test_offset_pagination_requests_every_page_until_total():
    session = FakeSession(
        [
            {"total": 250, "items": items(100)},
            {"total": 250, "items": items(100)},
            {"total": 250, "items": items(50)},
        ]
    )
    sleeps = []

    pages = list(iter_pages(session, "/api/indicators", "offset", sleep=sleeps.append))

    assert [p.number for p in pages] == [1, 2, 3]
    assert [len(p.records) for p in pages] == [100, 100, 50]
    assert [c["params"] for c in session.calls] == [
        {"limit": 100, "offset": 0},
        {"limit": 100, "offset": 100},
        {"limit": 100, "offset": 200},
    ]
    assert len(sleeps) == 2
    assert "offset=200" in pages[2].url


def test_offset_pagination_stops_on_empty_page():
    session = FakeSession([{"total": 500, "items": []}])

    pages = list(iter_pages(session, "/api/indicators", "offset", sleep=lambda _: None))

    assert len(pages) == 1
    assert len(session.calls) == 1


def test_http_errors_are_raised():
    session = FakeSession([FakeResponse({}, "https://datos.canarias.es/api/x", status_code=503)])

    with pytest.raises(requests.HTTPError):
        list(iter_pages(session, "/api/x", "none"))


def test_refuses_partial_loads_beyond_max_pages(monkeypatch):
    monkeypatch.setattr(http_source, "MAX_PAGES", 2)
    session = FakeSession([{"total": 1000, "items": items(100)}, {"total": 1000, "items": items(100)}])

    with pytest.raises(RuntimeError, match="partial load"):
        list(iter_pages(session, "/api/indicators", "offset", sleep=lambda _: None))


def test_session_retries_with_backoff_on_rate_limits_and_server_errors():
    retry = build_session().get_adapter("https://datos.canarias.es").max_retries

    assert retry.total == 5
    assert retry.backoff_factor == 2.0
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert retry.allowed_methods == frozenset({"GET"})
    assert retry.respect_retry_after_header is True
