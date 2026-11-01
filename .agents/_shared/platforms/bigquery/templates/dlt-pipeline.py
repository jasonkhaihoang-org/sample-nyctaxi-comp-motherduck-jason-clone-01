# ingestion/<pipeline_name>_pipeline.py  --  BigQuery domain (VD_DOMAIN_DATA_PLATFORM: bigquery)
#
# Placeholder. BigQuery dlt authoring is not supported yet: the plugin carries no
# BigQuery runtime package, so a generated pipeline from this file must not run. It
# stops with a plain message instead of falling back to another destination.
#
# RUN CONTRACT — this file is executed only by the `generating-dlt-pipeline`
# skill: your next tool call after committing this file is
# its sandbox-run step, never `python` on this file.
# A direct run skips the destination-identity assertion, the Tier-1 bronze
# gate and the preview.
raise SystemExit("BigQuery dlt pipelines are not supported yet")
