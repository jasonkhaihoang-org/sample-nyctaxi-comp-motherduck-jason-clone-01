# Databricks Dialect

## Sandbox destination

- A Domain binds a Unity Catalog production catalog and Primary Schema; each Intent writes to its mirror schema in the Domain's Ephemeral catalog, and reads of production stay in production.
- Resolve host, SQL warehouse path, catalog and schemas from `VD_DOMAIN_DATABRICKS_*` / `VD_EPHM_DATABRICKS_*` (`../../../lib/contracts/studio/runtime-contract.json`), never from a file or by listing.
- dbt adapter: `dbt-databricks` (`./dbt.md`).

## Null-safe comparison

Difference: `a IS DISTINCT FROM b`.
Equality: `a <=> b`, a synonym of `a IS NOT DISTINCT FROM b`.
