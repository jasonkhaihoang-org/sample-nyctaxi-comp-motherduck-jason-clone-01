# Sandbox run — dbt on Redshift

## Sandbox run

- Adapter `dbt-redshift`; target `ephemeral_dev`, the only one in Studio's profile, writes `VD_EPHM_REDSHIFT_DATABASE` on `VD_EPHM_REDSHIFT_HOST`.
- Run `dbt` plainly; `source /opt/runtime/bin/activate && dbt …` or `uv run dbt …` get no credential and fail.
- **No destination gate exists on the dbt path** (`assert_destination.py` is dlt-only).
  Read the database dbt actually connected to from its own output and confirm it equals `VD_EPHM_REDSHIFT_DATABASE` before recording evidence.
- `External tables are not supported in views` is a materialization error, not permissions: fix the config (§ Project config), do not retry.
- The sandbox starts **empty** (Primary Schema only), so a relation existing proves your run built it.
- A first connection after idle can take about a minute; wait once.
  A credential failure, `IAM authentication failed` against the sandbox, or a certificate error is an environment failure: report the message and stop.

## Defer

A production manifest is published, so every selected sandbox command carries `--defer --state /data/cache/prod-target` whenever `/data/cache/prod-target/manifest.json` exists. The sandbox holds only what this Intent builds, so a build without it has nothing to read for an upstream `ref()`.
When that manifest is absent, record defer unavailable and continue: its absence never shows the Domain is greenfield (the release may not have built one yet), and no command passes `--defer` without it.
This platform does not grant the path selection: select the model as the task names it, with plain `dbt`, never a `+model` closure to rebuild what defer reads. A changed ancestor outside that selection is read from production, so when the build defers one, say in the evidence and to the user that self-consistency with this Intent's changed ancestors was not checked.
A deferred `ref()` reads the Domain's relation across databases, as sources do, so a view over one needs `+bind: false` (`./dialect.md` § Cross-database reads); never add a defer macro of your own.

## Project config

Studio seeds no `dbt_project.yml`; author it with staging `+materialized: table`, and `+bind: false` where a view is wanted (`./dialect.md` § Cross-database reads).

## Unit tests

dbt-redshift refuses a `given` or `expect` fixture whose **first** row writes `null` for any column it lists (`does not have any row free of null values`): lead with a fully valued row and put the null case after it. A column the row leaves out is fine.

## Consumer layer

- A consumer (a query, report or app) reads a mart through a view; on Redshift build each one as a **late-binding view**, `+materialized: view` with `+bind: false`.
  By default dbt rebuilds a table by renaming the old one and dropping it with `CASCADE`, which removes every plain view bound to it, including views dbt does not manage.
- A late-binding view resolves its relations at query time, so a removed or renamed mart column fails only when the consumer runs: test the consumer (`./downstream-impact.md`) whenever a mart it reads changes its columns.
