"""HTTP extraction from the Gobierno de Canarias open-data APIs (datos.canarias.es)."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://datos.canarias.es"
USER_AGENT = "canarias-lakehouse/0.1 (data engineering portfolio project)"
RETRY_STATUSES = (429, 500, 502, 503, 504)
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
REQUEST_TIMEOUT_SECONDS = 300
PAGE_SIZE = 100
MAX_PAGES = 1000
PAUSE_BETWEEN_PAGES_SECONDS = 1.0


@dataclass(frozen=True)
class Page:
    number: int
    url: str
    records: list[Any]


def build_session() -> requests.Session:
    """Session that retries timeouts, connection errors, 429 and 5xx with exponential backoff.

    urllib3 waits BACKOFF_FACTOR * 2 ** (previous retries) seconds between attempts and honours
    the Retry-After header on 413, 429 and 503 responses.
    """
    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return session


def iter_pages(
    session: requests.Session,
    endpoint_path: str,
    pagination: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[Page]:
    """Yield every page of an endpoint.

    pagination="none": a single request; the whole JSON response is one record.
    pagination="offset": ISTAC list endpoints; `limit`/`offset` query parameters,
    records in `items` and the total record count in `total`.
    """
    url = f"{BASE_URL}{endpoint_path}"
    for index in range(MAX_PAGES):
        params = {"limit": PAGE_SIZE, "offset": index * PAGE_SIZE} if pagination == "offset" else None
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        if pagination == "none":
            yield Page(number=1, url=response.url, records=[payload])
            return
        records = payload["items"]
        yield Page(number=index + 1, url=response.url, records=records)
        if not records or (index + 1) * PAGE_SIZE >= int(payload["total"]):
            return
        sleep(PAUSE_BETWEEN_PAGES_SECONDS)
    raise RuntimeError(f"More than {MAX_PAGES} pages in {url}: refusing a partial load")
