# Databricks dbt

Dialect: `./dialect.md`.

## Sandbox run

Adapter `dbt-databricks`. Studio's profile is `dbt_databricks`, target `databricks_sandbox`: the Ephemeral catalog, with the Intent's mirror schema as dbt's target schema. The dbt shim supplies a fresh token per run and refuses a run that would write outside the Ephemeral catalog: report that error, never work around it. The agent never reads or sets a credential.

## Schema resolution

`macros/generate_schema_name.sql` (§ Project config) resolves every model, seed and snapshot; a data test keeps dbt's default schema. In prod and CI a node with no custom schema lands in the target schema (the Domain's Primary Schema) and a `+schema:` node in its named schema. In a sandbox the target schema is the Intent's own, which Studio created at activation and named with `VD_EPHM_SCHEMA_PREFIX`, and it is used unchanged; a `+schema:` node lands in `<prefix><name>`, which dbt creates as the driving user, who holds create-only rights on the shared Ephemeral catalog, so two Intents of a Domain cannot overwrite each other.
Studio's sandbox guard refuses to create a schema that does not start with the prefix: report the error, then copy the macro if it is missing, set a snapshot's `schema=` rather than `target_schema=`, or drop the `+schema:`; never work around the guard.
A malformed prefix, a schema name outside the logical-name grammar, or a name over 255 characters stops the run: report the error.
A snapshot must set `schema=`; the legacy `target_schema=` names the schema literally and bypasses the macro.

## Source reads

`macros/source_defer.sql` (§ Defer) defines the project's `source()` macro, so models call `{{ source() }}` as usual.
In a sandbox a source reads the Intent's prefixed schema in the target's (sandbox) catalog when it holds the table, and otherwise the Domain's table the sources YAML names; with no prefix, or without the macro, it reads the Domain's table.
A table an older pipeline version loaded into the prefixed schema is read as the Intent's own, and a schema name dlt shortened with a hash is not found, so that source falls back to the Domain table without a signal.
Only the Intent's primary schema is shared with its other members (extra ones: VD-7103), so for a member who did not create a prefixed schema the source falls back to the Domain table without a signal.

## Defer

A production manifest is published, so every selected sandbox command carries `--defer --state /data/cache/prod-target` whenever `/data/cache/prod-target/manifest.json` exists. The sandbox holds only what this Intent builds, so a build without it has nothing to read for an upstream `ref()`.
When that manifest is absent, record defer unavailable and continue: its absence never shows the Domain is greenfield (the release may not have built one yet), and no command passes `--defer` without it.
This platform grants the path selection: a partial model gate builds the model plus every changed or downstream-of-changed ancestor on its path against `/data/cache/prod-selection` and defers the rest to `/data/cache/prod-target`, with plain `dbt` as `../../references/guides/change-impact.md` § "The path selection for a partial run" gives it; both directories hold the same manifest.
dbt defers only `ref()`; a `source()` reads through `macros/source_defer.sql` (§ Source reads).
Before the first dbt command that compiles the project (`compile`, `show`, `build`), if it has no `macros/source_defer.sql`, copy `../_family/shared-container/templates/source_defer.sql` to it unchanged; never overwrite one that exists (§ Source reads).

## Project config

`profile:` is the literal `dbt_databricks`, Studio's profile name, in a first `dbt_project.yml` and in place of any other value: a Lakeflow dbt task names the profile it generates after the unrendered `profile:` text, so an `env_var` name is never found there.
Copy `../_family/shared-container/templates/generate_schema_name.sql` verbatim to `macros/generate_schema_name.sql` (§ Schema resolution).
Copy `macros/source_defer.sql` as § Defer says.
