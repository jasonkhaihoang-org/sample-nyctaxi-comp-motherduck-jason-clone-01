# Fabric Warehouse Dialect

Applies when `VD_DOMAIN_DATA_PLATFORM` is `fabric_warehouse`.
A Warehouse is its own platform, not a Lakehouse variant: dbt runs `dbt-fabric` over TDS (T-SQL) with no Spark, and dlt loads through the `fabric` destination (Parquet staging + `COPY INTO`).
Keep target choice in profiles and env indirection, never in model or pipeline logic.

## dbt Target

| Target | Identity | Writes to | Used by |
| --- | --- | --- | --- |
| `ephemeral_dev` | brokered token (`token_credential`, broker credential class) | Intent ephemeral Warehouse | Build-phase `dbt build` |

The profile resolves `server` from `VD_EPHM_FABRIC_WAREHOUSE_SQL_ENDPOINT`, `database` from `VD_EPHM_FABRIC_WAREHOUSE_NAME` and `schema` from `VD_EPHM_SCHEMA`.
Never author another target, hardcode those coordinates, or add a `driver:` key (dbt-fabric 1.11 picks the driver and rejects the field).

## T-SQL Authoring Rules

These are engine rejections, not style, and `dbt compile` catches none of them:

- `merge` is the default incremental strategy; **microbatch is unavailable**.
- **`CREATE VIEW` does not validate the view body**: a view with an invalid SELECT builds `[OK]` and fails only when queried. A green `dbt build` on a view model is not evidence; query every view you materialize.
- `expr::type` fails (`Incorrect syntax near '::'`); use `CAST(expr AS type)`.
- `current_timestamp()` fails: `CURRENT_TIMESTAMP` is niladic, so write it bare, or `SYSUTCDATETIME()`.
- There are no boolean literals: `= true` / `= false` fail; compare a `bit` to `1` / `0`.
- `timestamp` is `rowversion`, not a date/time type; it fails with `A table can only have one timestamp column…` then `The data type 'timestamp' … is not supported`. Write `datetime2(<precision>)`.
- `CAST(x AS datetime2)` without precision fails with `An integer precision value between 0 and 6 must be specified`; use `datetime2(6)` (the ceiling is 6, not 7).
- `datetime2` is the only persistable date/time type: `datetimeoffset` cannot be a persisted column, so convert timezone-aware sources explicitly.
- `nvarchar` / `nchar` do not exist; `varchar(max)` holds up to 16 MB and 8000 is the largest explicit length.
- `COPY INTO` does not coerce types, **appends**, needs the target table to exist, accepts only Entra ID auth from a OneLake source, and addresses items by **GUID**, not display name.
- Scalar functions are preview; multi-statement table-valued functions are unsupported.
- Do not rely on nested-CTE behaviour either way: dbt's adapter docs and Microsoft's T-SQL surface disagree.

## Deferred cross reads

Sources go through the project's copy of `./templates/source_defer.sql` (`./dbt.md` § Source reads); `ref()` needs no macro: `--defer` resolves it to the production name (`./dbt.md` § Defer), and the Ephemeral Paired Lakehouse takes the Domain Warehouse's name verbatim, so that name lands on the Ephemeral Paired Lakehouse.
Never add four-part quoted names or a defer macro of your own.

## Write Isolation

- `ephemeral_dev` writes only to the Intent's ephemeral Warehouse.
- dlt staging writes only to the Intent's Ephemeral Paired Lakehouse `Files/` area (`VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID`): Studio points `DESTINATION__FILESYSTEM__BUCKET_URL` there, shadowing the committed Domain location; `COPY INTO` lands in the ephemeral Warehouse.
- Never hardcode `VD_EPHM_*` ids, branch SQL by target, or edit Studio's profile to make one run pass.

## Orchestration

- A dbt workload runs through the job's dbt notebook (Warehouse template, `dbt-fabric` over TDS with the notebook identity), building into the target its delivered `profiles.yml` defaults to: `prod`, or `ephemeral_platform` in an Intent. Contract: `../_family/fabric/dbt-job-notebook.md`; sandbox sequence: `../_family/fabric/orchestration-sandbox-run.md` with Warehouse coordinates.
- The baked command is a full-project `dbt build`, so it carries the linter exclusion the Build persona's Runtime rules name.
- A Domain with a Paired Lakehouse commits its derived staging location: `./config-staging-section.md`.
- **The dlt leg is not a runner here**: the pipeline is its own notebook (`./pipeline-notebook.md`). Warehouse deltas: the destination table is `[destination.fabric]`; the default Lakehouse attachment is the Intent's **Ephemeral Paired Lakehouse** (code path only; a Warehouse has no `Files/`); the upload gets `VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID` and `VD_EPHM_FABRIC_WAREHOUSE_ID`.
- The in-Fabric dlt leg needs an `azure_key_vault` Domain (`../_family/fabric/dlt-runner-notebook.md`).

## Identity Boundary

- **Build:** container commands run under the brokered credential and write only to the Intent's ephemeral Warehouse and Ephemeral Paired Lakehouse. Never inspect, print, set or persist `FAB_TOKEN*`, `VD_CREDENTIAL_BROKER_URL`, `VD_CREDENTIAL_FILE` or `AZURE_CLIENT_ID`; an auth failure means re-login to Studio.
- **Deploy:** customer CI/CD; the plugin stops at PR-ready (`ciMode: 'none'`: no deploy lane carries a Warehouse artifact yet).

## Null-safe comparison

T-SQL has no boolean values to compare, so spell it out.
Null-safe difference: `(a <> b OR (a IS NULL AND b IS NOT NULL) OR (a IS NOT NULL AND b IS NULL))`.
Null-safe equality: `(a = b OR (a IS NULL AND b IS NULL))`.

## Schema fallback

Where the native schema tools are unavailable, read tables over TDS through the dbt sandbox target: a Warehouse has no `Tables` path, so `fab ls` lists items but not tables (`../_family/fabric/fab-cli-cheatsheet.md`).

## Sandbox destination

The ephemeral destination is `VD_EPHM_FABRIC_WAREHOUSE_WORKSPACE_ID` + `VD_EPHM_FABRIC_WAREHOUSE_ID` (TDS via `VD_EPHM_FABRIC_WAREHOUSE_SQL_ENDPOINT` + `VD_EPHM_FABRIC_WAREHOUSE_NAME`; dlt staging via `VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID`).
