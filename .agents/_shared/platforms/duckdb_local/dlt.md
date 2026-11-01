# Sandbox run — dlt on DuckDB

## Authoring

- Template: `./templates/dlt-pipeline.py`; for a `dlt-builtin` `filesystem` connection, `./templates/dlt-pipeline-local-files.py`.
- Destination literal: `"duckdb"`; `pipeline.run(source)` with no `table_format`.

## Destination

`duckdb`. Recommended auth method `duck_db`.

## Sandbox run

- Runtime distribution `vibedata-dlt-duckdb-studio`, imported as `vibedata.dlt.duckdb`.
- Secrets resolve from the Domain's Secret Store as `## Provider config` in `../../secret-stores/<secret-store>.md` says. A missing credential means run `add-or-update-source` again.
- `finalize()` is audit-only here; writes land directly.
- A schema-contract violation on the second run is surfaced to the user per the input rules of `../../references/guides/layer-roles.md`; never widen the contract silently.

## Full load

The database is a sandbox file, so the full load runs here: the sample-load command without `DLT_INGEST_LIMIT=<N>`, gated the same way.

## Destination identity

Report the resolved `VD_EPHM_DUCKDB_LOCAL_PATH`.

## Destination mismatch

A `destination ... differs from ... and will be ignored` or `state differs` warning means the load hit another file, typically dlt's cwd-relative `<pipeline_name>.duckdb`.

## Bronze tests

Connect through the `conftest.py` `duckdb_conn` fixture: a read-only connection to `VD_EPHM_DUCKDB_LOCAL_PATH`.

## Bronze preview

The wrapper reads the latest `data/*_bronze.duckdb`, groups dev-mode schemas by base name, and renders the canonical or latest schema.
