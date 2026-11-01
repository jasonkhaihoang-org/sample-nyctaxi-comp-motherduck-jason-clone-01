# Sandbox run — dlt on Redshift

## Authoring

- Template: `./templates/dlt-pipeline.py`; for a `dlt-builtin` `filesystem` connection, `./templates/dlt-pipeline-local-files.py`, a one-off load orchestration never invokes.
- Destination literal: `"redshift"`; the file carries no `DESTINATION__*` value, no credentials section and no database.
  A `duckdb` or `postgres` destination is refused by `assert_destination.py`.

## Destination

`redshift`. Recommended auth method `redshift`.

| Key | Value |
| --- | --- |
| `credentials.database` | `<VD_DOMAIN_REDSHIFT_DATABASE>` |
| `credentials.host` | `<VD_DOMAIN_REDSHIFT_HOST>` |
| `credentials.port` | `<VD_DOMAIN_REDSHIFT_PORT>` |
| `credentials.username` | `<VD_DOMAIN_REDSHIFT_USER>` |

## Sandbox run

- Host, port, database and username arrive as `DESTINATION__REDSHIFT__CREDENTIALS__{HOST,PORT,DATABASE,USERNAME}` from Studio.
- Keep `setup_environment()` first: it supplies the password only.
  Without it dlt raises `ConfigFieldMissingException` for the password, which is a dropped call, not a config gap.
  `RedshiftCredentialError` names the broker failure: report it and stop; never supply a password.
- TLS is set by `DESTINATION__REDSHIFT__CREDENTIALS__QUERY`, one JSON object; leave it, since dlt silently ignores a sub-key.
- Loads use `insert_values` row by row (no S3 staging is configured); slow is normal, and never add staging config.
- A load that connects at all landed in the sandbox, because the credential opens one database; the assertion confirms the family.
- The sandbox starts **empty**, so a table existing after the run is evidence.
- A first connection after idle can take about a minute; wait once.
  `IAM authentication failed` against the sandbox, a broker refusal or a certificate error is an environment failure: report and stop.

## Full load

The sandbox is the Intent's own database on the Domain's workgroup, so the full load runs here: the sample-load command without `DLT_INGEST_LIMIT=<N>`, gated the same way.
It inserts row by row (`## Sandbox run`), about 2,600 rows a second, so before a source of more than about a million rows, tell the user the expected time and offer a sample; run the full load only when they still want it.
The evidence, read with `lakehouse_query`, is this run's completed `audit_runs` row in the loaded dataset and each loaded table's `COUNT(*)`; the bronze suite stays deferred (`## Bronze tests`).
After a sample load into the same dataset, dlt resumes that sample's state: `first_run` is false and an incremental resource extracts only what the sample did not, so the table counts, not this run's extract count, show the full load.

## Destination identity

Report the database dlt reports connecting to.

## Bronze tests

A pytest suite cannot connect (the password is minted only for dlt and dbt); record a Tier 2/3 suite's execution as deferred.

## Bronze preview

The wrapper opens the sandbox through the Redshift script module, renders the schema `--dataset` names, and skips `_dlt*` and `audit_*` tables; a load leaves nothing on the container filesystem.
