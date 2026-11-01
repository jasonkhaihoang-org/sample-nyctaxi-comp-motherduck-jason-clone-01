# Snowflake dbt

Initial support: facts from the Studio Snowflake proposal (`docs/proposals/snowflake/`), not a verified run.

## Sandbox run

Adapter `dbt-snowflake`; the dbt shim supplies a fresh token per run, and the agent never reads or sets a credential.
Nothing further is specified.

## Defer

A production manifest is published, so every selected sandbox command carries `--defer --state /data/cache/prod-target` whenever `/data/cache/prod-target/manifest.json` exists. The sandbox holds only what this Intent builds, so a build without it has nothing to read for an upstream `ref()`.
When that manifest is absent, record defer unavailable and continue: its absence never shows the Domain is greenfield (the release may not have built one yet), and no command passes `--defer` without it.
This platform grants the path selection: a partial model gate builds the model plus every changed or downstream-of-changed ancestor on its path against `/data/cache/prod-selection` and defers the rest to `/data/cache/prod-target`, with plain `dbt` as `../../references/guides/change-impact.md` § "The path selection for a partial run" gives it; both directories hold the same manifest.
dbt defers only `ref()`; a `source()` reads the database and schema its sources YAML names; without them, the target's database and a schema named after the source.
