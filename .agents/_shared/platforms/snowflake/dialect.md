# Snowflake Dialect

Initial support: facts from the Studio Snowflake proposal (`docs/proposals/snowflake/`); no dialect recipes exist.

## Sandbox destination

- A Domain binds a production database and Primary Schema; each Intent gets its own empty database and role, and production reads use the user's own roles.
- Resolve account, host, warehouse and databases from `VD_DOMAIN_SNOWFLAKE_*` / `VD_EPHM_SNOWFLAKE_*` (`../../../lib/contracts/studio/runtime-contract.json`), never from a file or by listing databases.
- Identifiers keep their case (`direct` naming); quote one whose case matters.

## Null-safe comparison

Not specified: stop and report rather than guess.
