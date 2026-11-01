# Sandbox run — dbt on BigQuery

Initial support: no BigQuery sandbox build is recorded.

## Sandbox run

- Adapter `dbt-bigquery`; coordinates in `./dialect.md` § Sandbox destination.
- No Studio-seeded profile is recorded: read the target name from `$DBT_PROFILES_DIR/profiles.yml` before building.
- Pair `partition_by` with `cluster_by` and `require_partition_filter: true` on large models (`./dialect.md` § Cost guard).

## Schema resolution

`macros/generate_schema_name.sql` (§ Project config) resolves every model, seed and snapshot; a data test keeps dbt's default schema. In prod and CI a node with no custom schema lands in the target dataset (the Domain's Primary Schema) and a `+schema:` node in its named dataset. In a sandbox the target dataset is the Intent's own, which Studio created at activation and named with `VD_EPHM_SCHEMA_PREFIX`, and it is used unchanged; a `+schema:` node lands in `<prefix><name>`, which dbt creates as the driving user, who holds create-only rights on the shared Ephemeral project, so two Intents of a Domain cannot overwrite each other.
Studio's sandbox guard refuses to create a dataset that does not start with the prefix: report the error, then copy the macro if it is missing, set a snapshot's `schema=` rather than `target_schema=`, or drop the `+schema:`; never work around the guard.
A malformed prefix, a schema name outside the logical-name grammar, or a name over 255 characters stops the run: report the error.
A snapshot must set `schema=`; the legacy `target_schema=` names the dataset literally and bypasses the macro.

## Source reads

`macros/source_defer.sql` (§ Defer) defines the project's `source()` macro, so models call `{{ source() }}` as usual.
In a sandbox a source reads the Intent's prefixed dataset in the target's (sandbox) project when it holds the table, and otherwise the Domain's table the sources YAML names; with no prefix, or without the macro, it reads the Domain's table.
A table an older pipeline version loaded into the prefixed dataset is read as the Intent's own, and a dataset name dlt shortened with a hash is not found, so that source falls back to the Domain table without a signal.
Only the Intent's primary dataset is shared with its other members (extra ones: VD-7103), so for a member who did not create a prefixed dataset the source falls back to the Domain table without a signal.

## Defer

No production manifest is published, so never pass `--defer`. Nothing under `/data/cache` belongs to this Domain, so never list or read it.
Before the first dbt command that compiles the project (`compile`, `show`, `build`), if it has no `macros/source_defer.sql`, copy `../_family/shared-container/templates/source_defer.sql` to it unchanged; never overwrite one that exists (§ Source reads).

## Project config

No BigQuery project file is recorded yet; author `dbt_project.yml` when the first build runs.
Copy `../_family/shared-container/templates/generate_schema_name.sql` verbatim to `macros/generate_schema_name.sql` (§ Schema resolution).
Copy `macros/source_defer.sql` as § Defer says.

## See also

- `./dialect.md` — physical layout, the null-safe comparison and the cost boundary.
- `./dlt.md` — the dlt side, also initial.
