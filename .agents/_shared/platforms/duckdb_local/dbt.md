# Sandbox run — dbt on DuckDB

## Sandbox run

- Target `dev` writes the sandbox file at `VD_EPHM_DUCKDB_LOCAL_PATH`; the profile resolves it (`./dialect.md`).
- The sandbox path is the `VD_EPHM_DUCKDB_LOCAL_PATH` setting. If the setting is absent or its file is missing, halt and report a Studio provisioning failure; never create a database.
- The file admits one writer at a time: a probe left open can hold the lock a build needs.

## Inherited views

The sandbox is a renamed byte copy of the Domain database file, and a view stores the text of its query. Onboarding therefore checks every inherited view before any write, as its base setup says.

## Defer

No production manifest is published, so never pass `--defer`. Nothing under `/data/cache` belongs to this Domain, so never list or read it.
The sandbox already holds every Domain relation, so a deferred `source()` macro is not needed; if the repo has one, leave it alone.
