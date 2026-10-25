"""Test doubles for HTTP calls: no network in unit tests."""

from __future__ import annotations

from urllib.parse import urlencode

import requests


class FakeResponse:
    def __init__(self, payload, url: str, status_code: int = 200):
        self._payload = payload
        self.url = url
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error for {self.url}")


class FakeSession:
    """Returns the queued payloads in order and records every call."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        item = self._responses.pop(0)
        if isinstance(item, FakeResponse):
            return item
        full_url = f"{url}?{urlencode(params)}" if params else url
        return FakeResponse(item, full_url)
