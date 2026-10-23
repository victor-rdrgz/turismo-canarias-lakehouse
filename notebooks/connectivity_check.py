# Databricks notebook source
# Diagnostic notebook (ADR-0001): checks outbound connectivity from Databricks
# Free Edition serverless compute to each external data source before any
# ingestion is designed. Not part of the final Medallion pipeline.

import json
import time
import urllib.error
import urllib.request

# "verified_endpoint": True means this exact URL/params were already checked
# manually against the source's own docs or a real response outside Databricks.
# False means it is a best-effort base/metadata URL used only to test whether
# the domain is reachable from Free Edition; the real ingestion endpoint is
# still to be confirmed in SPEC.md / data contracts.
SOURCES = [
    {
        "name": "REE",
        "domain": "apidatos.ree.es",
        "url": (
            "https://apidatos.ree.es/es/datos/demanda/evolucion"
            "?start_date=2024-01-01T00:00&end_date=2024-01-02T00:00"
            "&time_trunc=hour&geo_trunc=electric_system&geo_limit=canarias&geo_ids=8742"
        ),
        "verified_endpoint": True,
    },
    {
        "name": "OMIE",
        "domain": "www.omie.es",
        "url": "https://www.omie.es/es",
        "verified_endpoint": False,
    },
    {
        "name": "AEMET",
        "domain": "opendata.aemet.es",
        "url": "https://opendata.aemet.es/opendata/api/maestro/municipios",
        "verified_endpoint": False,
    },
    {
        "name": "ISTAC",
        "domain": "datos.canarias.es",
        "url": "https://datos.canarias.es/api/estadisticas/statistical-resources/v1.0/datasets",
        "verified_endpoint": True,
    },
    {
        "name": "INE",
        "domain": "servicios.ine.es",
        "url": "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        "verified_endpoint": True,
    },
    {
        "name": "Aena",
        "domain": "www.aena.es",
        "url": "https://www.aena.es",
        "verified_endpoint": False,
    },
    {
        "name": "OpenSky",
        "domain": "opensky-network.org",
        "url": "https://opensky-network.org/api/states/all",
        "verified_endpoint": True,
    },
]

results = []
for source in SOURCES:
    row = {
        "source": source["name"],
        "domain": source["domain"],
        "url": source["url"],
        "verified_endpoint": source["verified_endpoint"],
    }
    start = time.time()
    try:
        req = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "canarias-lakehouse-connectivity-test/0.1"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(300)
            row.update(
                {
                    "status_code": resp.status,
                    "elapsed_ms": round((time.time() - start) * 1000),
                    "error": None,
                    "first_bytes": body.decode("utf-8", errors="replace")[:200],
                }
            )
    except urllib.error.HTTPError as e:
        body = e.read(300) if hasattr(e, "read") else b""
        row.update(
            {
                "status_code": e.code,
                "elapsed_ms": round((time.time() - start) * 1000),
                "error": f"HTTPError: {e.reason}",
                "first_bytes": body.decode("utf-8", errors="replace")[:200],
            }
        )
    except Exception as e:
        row.update(
            {
                "status_code": None,
                "elapsed_ms": round((time.time() - start) * 1000),
                "error": f"{type(e).__name__}: {e}",
                "first_bytes": "",
            }
        )
    results.append(row)

# COMMAND ----------

import pandas as pd

df = pd.DataFrame(results)
display(df)

# COMMAND ----------

dbutils.notebook.exit(json.dumps(results))
