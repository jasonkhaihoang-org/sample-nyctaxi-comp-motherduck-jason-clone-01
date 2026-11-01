# dbt on a Fabric Warehouse

## Sandbox run

- Adapter is `dbt-fabric` over TDS, not `dbt-fabricspark`; no Lakehouse guidance applies.
- The sandbox target is `ephemeral_dev` (TDS, `authentication: token_credential` through the broker credential class), the only target the profile carries. `prod` belongs to Domain CI's profiles; never recreate or run it from the sandbox.
- TDS connects in seconds; a hanging connection is a real problem to surface, not a warm-up.
- Never inspect or set `VD_CREDENTIAL_BROKER_URL` / `VD_CREDENTIAL_FILE` / `FAB_TOKEN*` / `AZURE_CLIENT_ID`. A 401 or login failure means the user must re-login to Studio.
- Never hardcode `VD_EPHM_*` ids, the SQL endpoint or the Warehouse name in models or the project file, never copy Domain coordinates into `VD_EPHM_*`, and never add target-conditional SQL. If the runtime env is incomplete or names a non-existent ephemeral Warehouse, halt and report the Studio provisioning issue.
- Read `./dialect.md` before authoring or fixing any model; its T-SQL rules are rejections.
- Verify relations with the native `lakehouse_schema` and `lakehouse_query` tools, which serve a Warehouse too. The ephemeral Warehouse, the Domain Warehouse and the Ephemeral Paired Lakehouse render under one name, so first list the ephemeral schema with `lakehouse_schema`. A relation this Intent built must be there, and `Invalid object name` for it is a real defect (wrong schema, wrong target, failed build): for a source, re-run the `dbt show` source check under the sandbox target; for a model, re-read the schema on the ephemeral target. A relation this Intent did not build is read through the Ephemeral Paired Lakehouse, which has no sync guarantee: reported missing, it may not have synced yet, so say so and tell the user to reopen the Intent, which re-mirrors the Ephemeral Paired Lakehouse, and never conclude it is absent. Never switch to DuckDB, `custom`, `prod`, or direct `fab` writes.
- Sources resolve through the project's `macros/source_defer.sql` (`## Source reads`); `ref()` needs no macro, and never add four-part names or a defer macro of your own.

`dbt compile` is **not** build evidence: it builds nothing, even when the adapter connects to compile.
A model that compiles and then fails `dbt build` is a model defect: report the failing SQL and the error verbatim, and never call it validated, production-ready, or blocked on the runtime.

## Defer

A production manifest is published, so every selected sandbox command carries `--defer --state /data/cache/prod-target` whenever `/data/cache/prod-target/manifest.json` exists. The sandbox holds only what this Intent builds, so a build without it has nothing to read for an upstream `ref()`.
When that manifest is absent, record defer unavailable and continue: its absence never shows the Domain is greenfield (the release may not have built one yet), and no command passes `--defer` without it.
This platform does not grant the path selection: select the model as the task names it, with plain `dbt`, never a `+model` closure to rebuild what defer reads. A changed ancestor outside that selection is read from production, so when the build defers one, say in the evidence and to the user that self-consistency with this Intent's changed ancestors was not checked.
Source reads to the Domain's relations are `macros/source_defer.sql`'s job (`## Source reads`), through the Ephemeral Paired Lakehouse that carries the Domain Warehouse's name (`./dialect.md` § Deferred cross reads); `ref()` needs no override.
Never add four-part names or a defer macro of your own.
Before the first dbt command that compiles the project (`compile`, `show`, `build`), if it has no `macros/source_defer.sql`, copy `./templates/source_defer.sql` to it unchanged; never overwrite one that exists.
The dbt job notebook defers with the production manifest too (`../_family/fabric/dbt-job-notebook.md`).

## Source reads

`macros/source_defer.sql` (`## Defer`) defines the project's `source()` macro, so models call `{{ source() }}` as usual; without it every source reads from the Domain through the Ephemeral Paired Lakehouse.
The sources YAML sets `database` to `VD_DOMAIN_FABRIC_WAREHOUSE_NAME`, and the Ephemeral Paired Lakehouse carries that name with each Domain schema mirrored onto it (ADR-0035), so the Domain table renders as `[<Ephemeral Paired Lakehouse>].[<schema>].[<table>]`.
In the sandbox (the target Warehouse is not the Domain's) a source reads the Intent's own table when the ephemeral Warehouse holds it; otherwise one `INFORMATION_SCHEMA.SCHEMATA` query on the Ephemeral Paired Lakehouse confirms the Domain schema is mirrored and the Domain table is read.
A Domain schema created after the Ephemeral Paired Lakehouse was last mirrored is not on it, so the compile stops with an error naming the source, the schema and the Ephemeral Paired Lakehouse: report it and tell the user to reopen the Intent, which re-mirrors the Ephemeral Paired Lakehouse; never create the schema or a shortcut yourself.
A missing table in a mirrored schema fails where the model reads it.

## Project config

Author `macros/generate_schema_name.sql` verbatim from `./templates/generate_schema_name.sql`: `dbt-fabric` has no schema macro of its own, so without it dbt joins the target schema and a custom `+schema` as `<target schema>_<custom>` on every target (`dbo_raw`, `dbo_staging`).
With it a node with no configured schema lands in the Domain's Primary Schema and a node with a `schema` config lands in that schema, identically in prod, CI and the sandbox.
A snapshot must set `schema`, not the legacy `target_schema`, which dbt applies verbatim and the macro never sees.
Copy `macros/source_defer.sql` as `## Defer` says.

## See also

- `./dialect.md`
