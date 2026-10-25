import pytest

from canarias_lakehouse.ingestion.config import IngestionConfig

VALID = {
    "endpoint_path": " /api/estadisticas/indicators/v1.0/indicators ",
    "dataset_name": "istac_indicadores_catalogo",
    "target_volume_path": "/Volumes/workspace/landing/gobierno_canarias/",
    "audit_table": "workspace.ops.ingestion_audit",
    "environment": "dev",
    "job_run_id": "123",
    "pagination": "offset",
}


def test_from_parameters_strips_and_normalises_values():
    config = IngestionConfig.from_parameters(VALID)

    assert config.endpoint_path == "/api/estadisticas/indicators/v1.0/indicators"
    assert config.target_volume_path == "/Volumes/workspace/landing/gobierno_canarias"
    assert config.pagination == "offset"
    assert config.job_run_id == "123"


def test_pagination_defaults_to_none():
    params = {k: v for k, v in VALID.items() if k != "pagination"}

    assert IngestionConfig.from_parameters(params).pagination == "none"


def test_missing_required_parameters_are_all_reported():
    params = {**VALID, "dataset_name": "", "audit_table": "  "}

    with pytest.raises(ValueError, match="dataset_name, audit_table"):
        IngestionConfig.from_parameters(params)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("endpoint_path", "api/no/leading/slash"),
        ("dataset_name", "Not-Snake-Case"),
        ("target_volume_path", "/Volumes/only/two"),
        ("target_volume_path", "/tmp/landing/x/y"),
        ("audit_table", "ops.ingestion_audit"),
        ("pagination", "page"),
    ],
)
def test_invalid_values_are_rejected(key, value):
    with pytest.raises(ValueError):
        IngestionConfig.from_parameters({**VALID, key: value})
