"""Validated parameters of one landing ingestion run."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

PAGINATION_MODES = ("none", "offset")
REQUIRED_PARAMETERS = ("endpoint_path", "dataset_name", "target_volume_path", "audit_table")

_DATASET_NAME = re.compile(r"[a-z0-9_]+")
_VOLUME_PATH = re.compile(r"/Volumes/[^/]+/[^/]+/[^/]+")
_TABLE_NAME = re.compile(r"[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+")


@dataclass(frozen=True)
class IngestionConfig:
    """Parameters of a run. Environment-specific values come from the bundle, never from code."""

    endpoint_path: str
    dataset_name: str
    target_volume_path: str
    audit_table: str
    environment: str = ""
    job_run_id: str = ""
    pagination: str = "none"

    @classmethod
    def from_parameters(cls, params: Mapping[str, str]) -> IngestionConfig:
        """Build a config from string parameters (job and task parameters) and validate it."""
        values = {key: (value or "").strip() for key, value in params.items()}
        missing = [name for name in REQUIRED_PARAMETERS if not values.get(name)]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        config = cls(
            endpoint_path=values["endpoint_path"],
            dataset_name=values["dataset_name"],
            target_volume_path=values["target_volume_path"].rstrip("/"),
            audit_table=values["audit_table"],
            environment=values.get("environment", ""),
            job_run_id=values.get("job_run_id", ""),
            pagination=values.get("pagination") or "none",
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.endpoint_path.startswith("/"):
            raise ValueError("endpoint_path must start with '/'")
        if not _DATASET_NAME.fullmatch(self.dataset_name):
            raise ValueError("dataset_name must be snake_case: [a-z0-9_]+")
        if not _VOLUME_PATH.fullmatch(self.target_volume_path):
            raise ValueError("target_volume_path must be /Volumes/<catalog>/<schema>/<volume>")
        if not _TABLE_NAME.fullmatch(self.audit_table):
            raise ValueError("audit_table must be <catalog>.<schema>.<table>")
        if self.pagination not in PAGINATION_MODES:
            raise ValueError(f"pagination must be one of {PAGINATION_MODES}")
