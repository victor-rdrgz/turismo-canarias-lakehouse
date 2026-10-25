# Databricks notebook source
# MAGIC %md
# MAGIC # Landing ingestion: Gobierno de Canarias API endpoint
# MAGIC
# MAGIC Entry point of the `ingest_gobierno_canarias_landing` job. The logic lives in
# MAGIC `canarias_lakehouse.ingestion` (unit tested); this notebook only reads parameters, runs the
# MAGIC ingestion and appends the audit row. Pattern: `docs/adr/0001-landing-ingestion-pattern.md`.
# MAGIC
# MAGIC Job parameters (from the bundle): `src_path`, `target_volume_path`, `audit_table`, `environment`, `job_run_id`.
# MAGIC Task parameters: `endpoint_path`, `dataset_name`, `pagination` (`none` or `offset`).

# COMMAND ----------

PARAMETERS = (
    "src_path",
    "endpoint_path",
    "dataset_name",
    "pagination",
    "target_volume_path",
    "audit_table",
    "environment",
    "job_run_id",
)
for name in PARAMETERS:
    dbutils.widgets.text(name, "")

# COMMAND ----------

# On serverless the working directory is not guaranteed, so the deployed src/ folder is added by absolute path.
import sys

src_path = dbutils.widgets.get("src_path").strip()
if not src_path:
    raise ValueError("src_path is required: absolute workspace path of the deployed src/ folder")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# COMMAND ----------

import json
import logging

from canarias_lakehouse.ingestion.audit import SCHEMA_DDL, create_table_statement
from canarias_lakehouse.ingestion.config import IngestionConfig
from canarias_lakehouse.ingestion.runner import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

config = IngestionConfig.from_parameters({name: dbutils.widgets.get(name) for name in PARAMETERS if name != "src_path"})
outcome = run_ingestion(config)

spark.sql(create_table_statement(config.audit_table))
spark.createDataFrame([outcome.audit.as_row()], SCHEMA_DDL).write.mode("append").saveAsTable(config.audit_table)

if outcome.error is not None:
    raise outcome.error

# COMMAND ----------

summary = outcome.summary()
if config.job_run_id:
    dbutils.jobs.taskValues.set(key="ingestion_summary", value=summary)
dbutils.notebook.exit(json.dumps(summary, ensure_ascii=False))
