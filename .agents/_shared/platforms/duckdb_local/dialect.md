# DuckDB Dialect

Applies when `VD_DOMAIN_DATA_PLATFORM` is `duckdb_local`.

## Sandbox destination

| Role | Coordinate | Rule |
| --- | --- | --- |
| Sandbox | `VD_EPHM_DUCKDB_LOCAL_PATH` | every write goes here |
| Domain | `VD_DOMAIN_DUCKDB_LOCAL_PATH` | read-only, never opened for writing |
| Source secrets | operator-managed dlt secrets under the domain data directory | never write plaintext secrets |

- Both paths are absolute and deployment-specific: take them from their settings, never type, remember or derive one.
- No tokens are involved.

## dbt targets

- The only target is `dev`, the sandbox file; there is no `prod` and no Domain attachment.
- Do not invent a target named `ephemeral`, and never author or edit a profile.
- The sandbox is a copy of the Domain database taken at activation, so `source()` and `ref()` both resolve inside it under their own schemas.
- `sources.yml` names schema and tables only, never a catalog.
- Deploy and post-merge runs belong to Domain CI and its bundle-owned profiles.

## Type fidelity

DuckDB does not coerce an expression to a contract's declared `data_type`, and `dbt compile` does not enforce contracts.
`date_trunc('week', ts)` returns `TIMESTAMP`; a `DATE` column must be `cast(date_trunc('week', ts) as date)`.
Cast every output expression to its declared type.

## Verification

Record command, exit code, artifact path, and `sha256` or row-hash for output comparisons.
Run `dbt_project_evaluator` only when the project's `packages.yml` installs it; when it is absent, do not select or `--exclude` it.

## Null-safe comparison

`a IS DISTINCT FROM b` / `a IS NOT DISTINCT FROM b`.
Plain `=` and `<>` yield NULL when either side is NULL.

## Session-local tabular tools

Native Studio data tools read local Parquet directly; do not convert it merely to admit it.
Apply the shared contract in `../../references/conventions/session-local-tabular-tools.md` for supported formats, sampling, processing budgets, and output limits.
