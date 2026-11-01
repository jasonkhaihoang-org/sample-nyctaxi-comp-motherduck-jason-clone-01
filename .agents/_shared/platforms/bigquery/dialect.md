# BigQuery Dialect

BigQuery support is initial: the platform is registered so the runtime contract and the platform gates agree with a Domain whose `VD_DOMAIN_DATA_PLATFORM` is `bigquery`. The layout and cost facts below are the platform's own and the practitioner pattern library's; the tool and coordinate facts are what the native tools do against a live BigQuery target.

## Reading and querying

The native `lakehouse_schema`, `lakehouse_query` and `export_query_data` tools connect to BigQuery: pass `target: "domain"` or `target: "ephemeral"` and read the schema and run bounded probes through them, as on every other supported platform.

- Each target's jobs run in that target's own project and location, and an unqualified table name resolves in that target's dataset. Domain is `VD_DOMAIN_BIGQUERY_PROJECT` with `VD_DOMAIN_BIGQUERY_PRIMARY_SCHEMA`; the Ephemeral is `VD_EPHM_BIGQUERY_PROJECT` with `VD_EPHM_BIGQUERY_DATASET`. Never write those values into a file.
- Name a relation either bare (`<table>`, which lands in the target's dataset) or fully qualified as `` `<project>.<dataset>.<table>` ``. Do not write a two-part `dataset.table` name: it resolves against the job's project, so it silently reads the wrong dataset whenever the dataset belongs to the other target. Quote the qualified name in backticks, because a project id may contain hyphens.
- Read columns with `lakehouse_schema` (`schemaType: "columns"`, optional `tableFilter`). Where you need `INFORMATION_SCHEMA`, qualify it with the dataset (`` `<project>.<dataset>`.INFORMATION_SCHEMA.COLUMNS ``), which is scoped to that dataset and therefore to its location. Use a region-qualified view (`region-<VD_DOMAIN_BIGQUERY_LOCATION lower-cased>.INFORMATION_SCHEMA.…`) only when the question spans datasets, because a job reads a dataset only from its own location.
- Run each profiling probe as its own aggregate, which returns one row. Output is capped at 256 KB: a larger result returns the leading rows with a `Results truncated` notice, so use aggregates or `LIMIT` rather than reading a table whole.
- A location mismatch fails the job, so report it as an environment failure rather than retrying in another region.

## Sandbox destination

- Domain: the project `VD_DOMAIN_BIGQUERY_PROJECT` and schema `VD_DOMAIN_BIGQUERY_PRIMARY_SCHEMA`. Read-only for plugin work.
- Sandbox: the project `VD_EPHM_BIGQUERY_PROJECT` and dataset `VD_EPHM_BIGQUERY_DATASET`. Every write goes here.
- Take every coordinate from its setting, never from a value written into a file and never by listing the catalog.

The dbt adapter is `dbt-bigquery`; the dlt destination literal is `bigquery`.

## Physical layout

`partition_by` is the cost boundary; `cluster_by` orders rows within a partition; `distkey` / `sortkey` do nothing.

## Cost guard

- Set `require_partition_filter: true` on a large partitioned model so an unfiltered query is rejected rather than scanning the table.
- Billing is on-demand (bytes scanned) or slot reservation (slot-hours): steady hourly loads suit slots, bursty ones on-demand; measure a month both ways.

## Null-safe comparison

Difference: `(a <> b OR (a IS NULL AND b IS NOT NULL) OR (a IS NOT NULL AND b IS NULL))`.
Equality: `(a = b OR (a IS NULL AND b IS NULL))`.
GoogleSQL has no `<=>`.
