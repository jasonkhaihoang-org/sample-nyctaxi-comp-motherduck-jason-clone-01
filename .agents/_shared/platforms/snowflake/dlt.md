# Sandbox run — dlt on Snowflake

Initial support: facts from the Studio Snowflake proposal (`docs/proposals/snowflake/`), not a plugin-side load.

## Authoring

- Template: `./templates/dlt-pipeline.py`.
- The template calls `register_secret_provider()` first, so source secrets resolve from the Domain's bound Secret Store, and ends each run with `persist_audit(..., table_format=None)`, which writes the `audit_*` tables to the schema.
- Destination literal `"snowflake"`; no credential, no `DESTINATION__*` value and no `staging=` argument.
- `dataset_name=dataset("<logical>")` is the Snowflake schema the raw layer lands in; the logical name is lowercase and naming is `direct`, so case is kept as written.

## Destination

`snowflake`. Recommended auth method `snowflake`.

| Key | Value |
| --- | --- |
| `credentials.database` | `<VD_DOMAIN_SNOWFLAKE_DATABASE>` |
| `credentials.host` | `<VD_DOMAIN_SNOWFLAKE_HOST>` |
| `credentials.warehouse` | `<VD_DOMAIN_SNOWFLAKE_WAREHOUSE>` |

## Sandbox run

- **The token is a file, never a value.** dlt reads the user's access token from a memory-only file only while all four hold:
  - `DESTINATION__SNOWFLAKE__CREDENTIALS__AUTHENTICATOR` is `oauth`;
  - no token, password or key is configured anywhere (no `…__TOKEN`, no `secrets.toml` entry);
  - `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_HOST` are both set;
  - the token file is present.

  Adding any credential to fix a login error switches dlt off the file: report the error and stop.
- Database and role come from `VD_EPHM_SNOWFLAKE_DATABASE` / `VD_EPHM_SNOWFLAKE_ROLE`, published as `DESTINATION__SNOWFLAKE__CREDENTIALS__{DATABASE,ROLE}`; under the ambient posture no role is set and the user's default applies.
- Loads `PUT` into each table stage (`@%<table>`) then `COPY INTO`; configure no bucket or stage.
- The load creates an absent schema, owned by the Intent role.
- The sandbox starts **empty**, so a table existing after the run is evidence.

## Destination identity

Report the database dlt connects to; the assertion compares family and, when persisted, the Intent database and role.

## Bronze tests

Not yet specified.

## Bronze preview

The wrapper opens the Intent database through the Snowflake script module, renders the first rows of each table outside `INFORMATION_SCHEMA`, skips `_`-prefixed and `audit_*` tables, and says when it stops at its table limit.
