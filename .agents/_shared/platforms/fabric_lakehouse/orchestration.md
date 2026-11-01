# Orchestration — Fabric Lakehouse

The native items are a Data Pipeline (`orchestration/<Name>.DataPipeline/`) or Apache Airflow Job (`orchestration/<Name>.ApacheAirflowJob/`); a dbt workload runs through its own `orchestration/<job>_dbt.Notebook/`.

## Intent

Follow `## Intent` in `../_family/fabric/orchestration-stages.md`.

## Design

Follow `## Design` in `../_family/fabric/orchestration-stages.md`.

## Plan

Follow `## Plan` in `../_family/fabric/orchestration-stages.md`. Delta: a Data Pipeline dlt activity invokes the committed pipeline notebook `ingestion/<name>_pipeline.Notebook/`; Generate authors no dlt runner for it.

## Verify

Follow `## Verify` in `../_family/fabric/orchestration-stages.md`.

## Ship

Follow `## Ship` in `../_family/fabric/orchestration-stages.md`.

## Authoring

Follow `../_family/fabric/orchestration-authoring.md`. Delta: there is no dlt runner on a Data Pipeline: the pipeline notebook at `ingestion/<name>_pipeline.Notebook/` is the item a dlt activity invokes, and it takes `DOMAIN_SLUG` alone. A dbt activity invokes its job's dbt notebook, materialized with `--platform lakehouse`.

## Sandbox run

Follow `../_family/fabric/orchestration-running.md`. Delta: import the pipeline notebook `ingestion/<name>_pipeline.Notebook/` for each dlt activity; every upload is given `VD_EPHM_FABRIC_LAKEHOUSE_ID` with no Warehouse id.

## Evaluate

Follow `../_family/fabric/orchestration-evaluating.md`.

## Document

Follow `../_family/fabric/orchestration-documenting.md`.
