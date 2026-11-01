# Redshift Dialect

PostgreSQL-descended; dbt adapter `dbt-redshift`, dlt destination `redshift`.

## Sandbox destination

| Role | Coordinates | Rule |
| --- | --- | --- |
| Sandbox | `VD_EPHM_REDSHIFT_DATABASE` on `VD_EPHM_REDSHIFT_HOST`:`VD_EPHM_REDSHIFT_PORT`, user `VD_EPHM_REDSHIFT_USER`, Primary Schema `VD_EPHM_SCHEMA` | every write goes here; TLS pinned by `DESTINATION__REDSHIFT__CREDENTIALS__QUERY` |
| Domain | `VD_DOMAIN_REDSHIFT_DATABASE`, schema `VD_DOMAIN_SCHEMA` | read-only, reached only by three-part name |
| Compute | exactly one of `VD_EPHM_REDSHIFT_WORKGROUP_NAME` (Serverless) or `VD_EPHM_REDSHIFT_CLUSTER_IDENTIFIER` (provisioned) | not needed to connect |

- Take every coordinate from its setting; never write a host, database or user into a file or find one by listing.
- A credential opens exactly one database: connecting the sandbox credential to the Domain fails with `IAM authentication failed`, by design.
  Read Domain tables as `<domain_database>.<schema>.<table>`.

## Credentials

Only two paths obtain a credential:

- dbt: run `dbt` plainly; the shim mints a password into that one process.
  The profile is Studio's at `$DBT_PROFILES_DIR/profiles.yml`, target `ephemeral_dev`, profile name the Intent's `DBT_PROFILE_NAME` (read by `dbt_project.yml`); never guess the name, read its values or write a profile.
- dlt: `setup_environment()` supplies the password only; host, port, database and username are published under dlt's own names.

- The user is a coordinate, not a secret; on Serverless it reads `IAMR:<role>` and **contains a colon**, so pass it as a field, never inside a URL.
- Never read, print, set, export, persist or pass a credential on a command line.
- Report the command, exit code and stderr, then stop, on a broker refusal, `IAM authentication failed` against the sandbox itself, or a TLS/certificate error.
- `DESTINATION__REDSHIFT__CREDENTIALS__QUERY` is one JSON object (`sslmode` + trust-store path); never loosen it or add a sub-key.
- An idle Serverless workgroup takes 30–60 seconds to resume: wait once; a second failure is a report.

## Cross-database reads

- The profile's `datasharing: true` makes a cross-database `source()` resolve; never remove it or replace the profile.
- A model over a Domain relation must be a **table or a late-binding view**: a plain view fails with `External tables are not supported in views`.
  Default staging to `+materialized: table`; for a view use `+bind: false` on the folder or `{{ config(bind=False) }}`.

## Incremental strategy

`merge` is supported (default), with `append`, `delete+insert` and `microbatch`.

## Keys

No clustering: physical layout is `sortkey` and `distkey` / `diststyle`; `cluster_by` does nothing.

## Isolation

A session can read another Intent's sandbox by three-part name; claim no per-Intent isolation, and scope reads to `VD_DOMAIN_REDSHIFT_DATABASE` or the sandbox.

## Verification

**No destination gate exists on the dbt path**: read the database from dbt's own output; dlt's is asserted by `assert_destination.py`.

## Null-safe comparison

Difference: `(a <> b OR (a IS NULL AND b IS NOT NULL) OR (a IS NOT NULL AND b IS NULL))`.
Equality: `(a = b OR (a IS NULL AND b IS NULL))`.

## Schema fallback

Without the native schema tools, use `dbt show --inline` on the sandbox target.
`information_schema.tables` covers only the sandbox; list Domain relations from `svv_redshift_tables` where `database_name` is `VD_DOMAIN_REDSHIFT_DATABASE`.
