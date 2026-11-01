# MotherDuck Dialect

The DuckDB engine: SQL, the `dbt-duckdb` adapter and the dlt destination family match DuckDB.
Never read `../duckdb_local/dialect.md` here; its paths and credential-free identity are wrong for MotherDuck.

## Sandbox destination

| Role | Coordinate | Rule |
| --- | --- | --- |
| Sandbox | `VD_EPHM_MOTHERDUCK_DATABASE` | every write goes here; dbt opens it as `md:<database>`, dlt composes that form itself |
| Domain | `VD_DOMAIN_MOTHERDUCK_DATABASE` | read-only, and nothing but the profile's single `dev` target enforces it |

- `VD_EPHM_MOTHERDUCK_DATABASE` unset means the Intent has no sandbox (some Intents reach the Domain database alone): halt and report; never build or load, and never substitute the Domain database.
- `VD_EPHM_DUCKDB_LOCAL_PATH` / `VD_DOMAIN_DUCKDB_LOCAL_PATH` do not exist here; resolving one means you are on the wrong platform.
- Take the database from its setting only, never hardcoded and never by listing the catalog.
- **Silent failure:** a relative `md:` string passed as a plain connection value becomes a local file path, and the load still reports success with correct row counts.
  dlt has a gate for it; dbt does not (`./dbt.md`).

## Credentials

Only two paths obtain a credential:

- dbt: run `dbt` plainly; `source /opt/runtime/bin/activate && dbt …` or `uv run dbt …` get no credential and fail.
- dlt: `setup_environment()` in a pipeline that runs in this container; keep the call. The Flight artifact carries none (`./dlt.md` § Pipeline artifact).

`motherduck_token` in the environment is a placeholder: an ad-hoc `duckdb.connect("md:…")`, `duckdb` CLI or self-written script fails authentication in about two seconds by design.
Introspect with the native `lakehouse_schema` / `lakehouse_query` tools (`target: domain` or `ephemeral`); vendor tools only for what they alone cover (`./vendor-tools.md`).
Never read, print, set, export, persist or pass a credential on a command line.

Report the command, exit code and stderr, then stop, on a broker refusal, a 401 or permission error, or a client-version refusal (report the version MotherDuck named; the image pins `duckdb`).
Never re-auth, install another `duckdb` wheel, or fall back to a local file.

## Access and catalog

- Access is account-wide for the credential's identity; there is no per-database write grant, only `GRANT READ ON SHARE`.
  Do not try to narrow access in SQL or report a grant never issued.
- `ATTACH 'md:<db>' (READ_ONLY)` under a read-write credential is procedural only; record it as a degradation.
- A received share is read-only; a successful `USE` or `SELECT` proves nothing about write access.
- `SHOW DATABASES` lists the acting identity's databases across all Domains and Intents; another identity's database is absent, not denied, and the same name can exist under two identities.
- Never create, drop, rename or attach databases; Studio owns the sandbox lifecycle.

## The sandbox starts full

- The sandbox is a zero-copy clone of the Domain taken at activation; plan against real data, never rebuild Domain tables.
- A relation existing proves nothing about your run; take evidence from the load package, `audit_runs` / `audit_table_loads` and dbt run results.
- Data landed in the Domain after activation is not in the clone.
- An empty sandbox on a running Intent is an anomaly to report.

## dbt targets

The only target is `dev`; do not invent `ephemeral`, and never author or edit a profile.
Domain CI alone reaches the Domain database, with its bundle-owned profiles.

## Verification

Row evidence alone is never sufficient: pair every load's evidence with the database the connection actually opened.
Run `dbt_project_evaluator` only when the project's `packages.yml` installs it.

## Null-safe comparison

`a IS DISTINCT FROM b` / `a IS NOT DISTINCT FROM b`; plain `=` and `<>` yield NULL when either side is NULL.

## See also

- [`./audit-surfaces.md`](./audit-surfaces.md) — runtime-audit read surfaces.
