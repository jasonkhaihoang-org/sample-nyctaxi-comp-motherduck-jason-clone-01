# dbt on a Fabric Lakehouse

## Sandbox run

- The sandbox target is `ephemeral_dev` (Livy, `token_credential` through the broker), the only target the rendered profile carries. Never run `prod` or `ephemeral_platform` from the sandbox (`./dialect.md` § dbt Targets).
- The sandbox profile reuses one Spark session across the Intent's dbt commands. The first command starts it, which can take several minutes on a cold capacity; wait for it, and do not run other commands in parallel or offer alternatives meanwhile. A later command reuses it within seconds unless the session sat idle past its timeout, so a slow command right after another one is not a cold start: read its output for the cause. A Fabric item run (a notebook or pipeline job) is not a sandbox command: each of its dbt commands opens its own session.
- Every dbt command except `parse`, `ls`, `deps`, `clean` and `init` opens the session, so it can take minutes, longer than the blocking terminal waits. Launch it with `start_async_bash` and `timeout_seconds: 1800` (the default 300 kills a command that includes the session start), then call `wait_for_async_bash` on that handle with `wait_timeout_seconds: 300`, repeating while it reports the task still running.
- Never inspect or set `VD_CREDENTIAL_BROKER_URL` / `VD_CREDENTIAL_FILE` / `FAB_TOKEN*` / `AZURE_CLIENT_ID`. A 401 from `dbt` or `fab` means the user must re-login to Studio.
- Never hardcode `VD_EPHM_*` ids in models or the project file, never copy Domain ids into `VD_EPHM_*`, and never add target-conditional SQL. If the runtime env is incomplete or names a non-existent ephemeral Lakehouse, halt and report the Studio provisioning issue.
- A source resolves in the Ephemeral Lakehouse and, under `--defer`, falls back to the Domain's through `macros/source_defer.sql` (`## Defer`); nothing copies Domain tables into the Ephemeral Lakehouse.
- Never create a shortcut to make a source readable: `create_shortcuts` serves only downstream-impact testing (`./downstream-impact.md`).
- On `TABLE_OR_VIEW_NOT_FOUND` for a source, check that the build ran with `--defer` and that the macro exists; re-run the `dbt show` source check under the sandbox target with `--defer --state /data/cache/prod-target`. Never switch to DuckDB, `custom`, `prod`, or direct `fab` writes.

## Defer

A production manifest is published, so every selected sandbox command carries `--defer --state /data/cache/prod-target` whenever the validated manifest is present. The sandbox holds only what this Intent builds; a build without it reads the Ephemeral Lakehouse for every upstream model and fails `TABLE_OR_VIEW_NOT_FOUND`.
The CD release's `manifest_prod.json` is the target manifest and its placeholder-identifier `manifest.json` the selection manifest.
This platform grants the path selection: a partial model gate builds the model plus every changed or downstream-of-changed ancestor on its path against `/data/cache/prod-selection` and defers the rest to `/data/cache/prod-target`, with plain `dbt` as `../../references/guides/change-impact.md` § "The path selection for a partial run" gives it.
dbt defers only `ref()`, so a `source()` needs `macros/source_defer.sql`, which reads the Domain's workspace off the production manifest's released models.
Before the first dbt command that compiles the project (`compile`, `show`, `build`), if it has no `macros/source_defer.sql`, copy `./templates/source_defer.sql` to it unchanged; never overwrite one that exists.
A Domain with no released model gives the macro nothing to defer to: report that rather than staging the source.
To verify defer, list the dev schema's tables with `fab ls` (`../_family/fabric/fab-cli-cheatsheet.md`).

## Project config

- Copy `./templates/source_defer.sql` to `macros/source_defer.sql` when the project has none (`## Defer`).
- Author `macros/generate_schema_name.sql` verbatim from `./templates/generate_schema_name.sql`: without it `dbt-fabricspark` honours a custom `+schema` only on a target named `prod`, so sandbox and Intent runs put every model in one schema and defer breaks.
- Delete any `macros/fabricspark_generate_schema_name_for_env.sql`: the adapter never calls it.
