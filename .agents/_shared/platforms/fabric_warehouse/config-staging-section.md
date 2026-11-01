# The staging section — `fabric_warehouse`

Write into `ingestion/.dlt/config.toml`, beside `[destination.fabric]`.

## Derived from the Paired Lakehouse, never asked

A Warehouse load writes row by row unless the connection names somewhere to stage.
The Domain's Paired Lakehouse is that place, so the location is derived from two Domain settings and the user is asked nothing: `VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_ID` and `VD_DOMAIN_FABRIC_WAREHOUSE_CODE_LAKEHOUSE_ID`.
dlt states a staging location as a filesystem destination:

```toml
[destination.filesystem]
bucket_url = "abfss://<VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_ID>@onelake.dfs.fabric.microsoft.com/<VD_DOMAIN_FABRIC_WAREHOUSE_CODE_LAKEHOUSE_ID>/Files/staging"
```

This `bucket_url` names where the parquet waits, not where the load lands, and the table carries no ids.
Write it once, substituting the two values; derive and create nothing else.

- **A `bucket_url` already committed and equal to the derived one** stays untouched. Compare ignoring case and a trailing slash, and call it differing only when it still differs.
- **A committed `bucket_url` that differs** is a location someone chose earlier: tell the user which location the config held and which one you used, replace it with the derived one, and say so.
- **`VD_DOMAIN_FABRIC_WAREHOUSE_CODE_LAKEHOUSE_ID` or `VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_ID` is unset**: treat the Domain as unpaired. Say the Domain has no Paired Lakehouse and that loads are row by row until one is set in Domain settings; write no section and leave any committed one as it is.
