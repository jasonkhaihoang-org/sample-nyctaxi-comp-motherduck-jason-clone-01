# Fabric Lakehouse Dialect

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

Applies when `VD_DOMAIN_DATA_PLATFORM` is `fabric_lakehouse`: dbt runs `dbt-fabricspark` (Spark SQL over Livy).
Keep target choice in profiles and env indirection, never in model or pipeline logic.

## dbt Targets

| Target | Identity | Writes to | Lives in | Used by |
| --- | --- | --- | --- | --- |
| `ephemeral_dev` | user delegated token | Intent ephemeral Lakehouse | the profile Studio renders at Open (the only sandbox target, `./dbt.md`) | Build-phase `dbt build` |
| `ephemeral_platform` | workspace identity | Intent ephemeral Lakehouse | the Intent's `~/fab_notebook_profile/profiles.yml` | the dbt job notebook's sandbox run |
| `prod` | workspace identity | Domain Lakehouse | the committed `transformation/profiles.yml` | the dbt job notebook in the Domain workspace |

There is no target named `ephemeral`; profile details are `../_family/fabric/dbt-job-notebook.md` § "The profile".
Never hardcode `VD_EPHM_*` ids, branch SQL by target, add project-level `+workspace_name` macros, or edit Studio's profile to make one run pass.

The Fabric `dbt_project.yml` keeps Elementary installed for test macros but disables its artifact autoload, so builds pass or fail on user models and tests only.

## Runtime Contract

- Run `dbt <dbt args>`, `fab` and `papermill` directly in the intent workspace.
- The notebook's deploy command is a full-project `dbt build`, so it carries the project-quality linter exclusion the Build persona's Runtime rules name.
- The dbt credential module and the `vdfab` shim mint tokens per call through Studio's runtime access (`vd credential get`). Never inspect, print, set or persist `FAB_TOKEN*`, `VD_CREDENTIAL_BROKER_URL`, `VD_CREDENTIAL_FILE` or `AZURE_CLIENT_ID`. A 401 means the user must re-login to Studio.

## Fabric Spark catalog blocked (diagnostic)

If `dbt debug` succeeds but a later command fails on Spark catalog metadata (`Failed to get database metadata`, or a 30s `flatMap` timeout from `show schemas` / `show tables` / CTAS), do not change broker env or switch to DuckDB.
Run `$SKILL_DIR/../../scripts/platforms/fabric_lakehouse/vd-fabric-onelake-delta.py` with `VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID`, `VD_EPHM_FABRIC_LAKEHOUSE_ID` and `VD_EPHM_SCHEMA` to check the broker storage lane; if it succeeds, report `FABRIC_SPARK_CATALOG_BLOCKED`.
The helper is diagnostic only; dbt stays the build path.

## Orchestration

Contracts live under `../_family/fabric/`: the dbt job notebook in `../_family/fabric/dbt-job-notebook.md`, the sandbox sequence in `../_family/fabric/orchestration-sandbox-run.md`.
**The dlt leg is not a runner here**: the pipeline is its own notebook (`./pipeline-notebook.md`).
Lakehouse deltas: the load runs in the notebook kernel, the destination table is `[destination.filesystem]`, the default Lakehouse attachment is the Domain's own Lakehouse, and the upload gets `VD_EPHM_FABRIC_LAKEHOUSE_ID` with no Warehouse id.
The in-Fabric dlt leg needs an `azure_key_vault` Domain (`../_family/fabric/dlt-runner-notebook.md`).

## Identity Boundary

- **Build:** container commands run under the user's delegated token and write only to the Intent ephemeral Lakehouse.
- **Verify:** the Fabric notebook and pipeline run in the ephemeral workspace under workspace identity.
- **Deploy:** post-merge tooling owns production deploy; the plugin stops at PR-ready.

## Project audit

Spark cannot parse `dbt_project_evaluator`'s recursive `int_all_dag_relationships` model, so the evaluator fails in the sandbox whatever the project holds. Do not run the transformation playbook's Project audit here: record it `not applicable: the evaluator's recursive model does not parse on Spark`, and cite the Domain's own offline evaluator run when its CI has one.

## Null-safe comparison

Spark SQL's null-safe equality is `a <=> b` (true when both are NULL); a null-safe difference is `NOT (a <=> b)`.
Plain `=` and `<>` yield NULL when either side is NULL.

## Read-back models are tables

The native `lakehouse_query` and `lakehouse_schema` tools read through the Lakehouse's SQL analytics endpoint, which exposes Delta tables only. dbt-fabricspark builds a model as a Spark view by default, and a Spark view is never visible at the endpoint, so a read of it fails with `Invalid object name` however long you wait. Set `materialized: table` (in the model's `config()` or under `models:` in `dbt_project.yml`) on every model the agent must read back through the SQL tools, such as a mart that a probe or a test reads. A table that is present in the Spark metastore but briefly absent at the endpoint is sync lag instead, covered in [`./audit-surfaces.md`](./audit-surfaces.md).

## Querying the SQL endpoint

`lakehouse_query` runs T-SQL against the SQL analytics endpoint, not the Spark SQL the models are written in, so write each read in T-SQL:

| Spark SQL in the models | T-SQL for `lakehouse_query` |
| --- | --- |
| `date_trunc('month', ts)` | `DATETRUNC(month, ts)` |
| `date '2024-01-15'` | `CAST('2024-01-15' AS date)` |
| `where is_billable` (a boolean) | `WHERE is_billable = 1` (the endpoint exposes a boolean as `bit`) |
| `a <=> b` | `(a = b OR (a IS NULL AND b IS NULL))` |
| `limit 10` | `SELECT TOP 10` |
| `` `schema`.`table` `` (backtick identifiers) | `[schema].[table]` |
| `show schemas`, `show tables` | `INFORMATION_SCHEMA.SCHEMATA`, `INFORMATION_SCHEMA.TABLES` |

Read a table's columns with `lakehouse_schema` before querying it rather than guessing names.
After a build, call `refresh_sql_metadata` before the first `lakehouse_query` of a table that build created or replaced: the endpoint learns of a new Delta table lazily, and a read before the refresh answers `Invalid object name` (sync lag, `./audit-surfaces.md`).

## Schema fallback

Where the native schema tools are unavailable, list the Lakehouse's tables with `fab` per the `List Lakehouse tables` recipe in `../_family/fabric/fab-cli-cheatsheet.md`.

## Sandbox destination

The ephemeral destination is `VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID` + `VD_EPHM_FABRIC_LAKEHOUSE_ID`.
