# Sandbox run — dlt on BigQuery

Initial support: the plugin has no BigQuery runtime package.

## Authoring

- Template: `./templates/dlt-pipeline.py`, a placeholder that only refuses.
- Destination literal `"bigquery"`; the file carries no credential and no `DESTINATION__*` value.

## Destination

BigQuery dlt ingestion is not supported yet.

## Sandbox run

Never execute a generated pipeline: there is no runtime package.
For schedule cost, see `./dialect.md` § Cost guard.

## Destination identity

Not yet specified; there is no identity to assert.

## Bronze tests

Not yet specified.

## Bronze preview

Not yet specified.
