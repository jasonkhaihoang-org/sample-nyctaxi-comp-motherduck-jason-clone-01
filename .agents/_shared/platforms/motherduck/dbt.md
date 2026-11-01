# Sandbox run — dbt on MotherDuck

## Sandbox run

- Adapter `dbt-duckdb`; target `dev` writes `md:<database>` for `VD_EPHM_MOTHERDUCK_DATABASE`, resolved by the profile.
- `VD_EPHM_MOTHERDUCK_DATABASE` unset: halt and report; do not build.
- **No destination gate exists on the dbt path** (`assert_destination.py` is dlt-only).
  Read the database dbt actually connected to from its own output and confirm it equals `VD_EPHM_MOTHERDUCK_DATABASE` before recording evidence.
- Run `dbt` plainly; activated or `uv run` binaries get no credential (`./dialect.md` § Credentials).
- There is no sandbox file: never `test -f` or `ls` for a `.duckdb`; the sandbox is proven by connecting.
- The sandbox is a Domain clone, so take evidence from the build's run results, not from a relation existing.
- Never point a run at the Domain database by target, flag or self-opened connection.
- A credential, permission or client-version failure is an environment failure: report the exact message and stop; never install another `duckdb` wheel or retarget to a local file.

## Defer

A production manifest is published: the CD release's manifest is both the target and the selection manifest.
This platform grants the path selection: a partial model gate builds the model plus every changed or downstream-of-changed ancestor on its path against `/data/cache/prod-selection` and defers the rest to `/data/cache/prod-target`, with plain `dbt` as `../../references/guides/change-impact.md` § "The path selection for a partial run" gives it; both directories hold the same manifest.
The sandbox clones the Domain, so an unselected ancestor already exists there as production's copy; only the path selection rebuilds a changed one.
List the dev schema with `SHOW TABLES` when verifying defer.
