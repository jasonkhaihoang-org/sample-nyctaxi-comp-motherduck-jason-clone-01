# dlt on a Fabric Lakehouse

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

## Authoring

- The pipeline is a Fabric notebook item, not a script: scaffold it with `./pipeline-notebook.md` § Generate instead of writing `ingestion/<name>_pipeline.py`. The rest of the layout (`sources/`, `requirements.txt`) is unchanged.
- The destination literal is `"filesystem"`.
- A notebook is executed, never imported: the load runs flat in its own cell, so validate its entry point by reading the file, not importing it.
- Delta `merge` does not deduplicate: `dedup_sort` has no effect and there is no `delete-insert`. The first load into a new table lands every repeated key. A later merge whose source repeats a key fails with `MERGE matched a target row with multiple source rows`. A merge into a table that already holds a repeat rewrites every copy and keeps the repeat.
- A repeated key follows `../../references/guides/duplicate-keys.md`; `merge` here does not deduplicate.

## Destination

`filesystem`. Recommended auth method `azure`, dlt's Azure credentials: give it the account name and host below and leave `azure_storage_sas_token` empty, and dlt falls back to the default credential — a Fabric notebook signs in as its own identity, the sandbox through Studio's broker.

| Key | Value |
| --- | --- |
| `workspace_id` | `<VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_ID>` |
| `lakehouse_id` | `<VD_DOMAIN_FABRIC_LAKEHOUSE_ID>` |
| `bucket_url` | `abfss://<VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_ID>@onelake.dfs.fabric.microsoft.com/<VD_DOMAIN_FABRIC_LAKEHOUSE_ID>/Tables` |
| `credentials.azure_storage_account_name` | `onelake` |
| `credentials.azure_account_host` | `onelake.blob.fabric.microsoft.com` |

## Sandbox run

- Runtime distribution: `vibedata-dlt-fabric-studio` (import `vibedata.dlt.fabric`). Dialect: `destination="filesystem"`, `pipeline.run(source, table_format="delta")`.
- Never inspect, set or edit `FAB_TOKEN*` or `AZURE_CLIENT_ID`. A 401 means the user must re-login to Studio.
- Secrets resolve from the Domain's Secret Store, connection-keyed; the pipeline file names no store or secret, and the committed config carries what `## Provider config` in `../../secret-stores/<secret-store>.md` gives.
- dlt writes to the Lakehouse named by `[destination.filesystem] bucket_url` (§ Destination). The Lakehouse must be schema-enabled: dlt writes `Tables/<dataset>/<table>`, which a non-schema Lakehouse shows as Unidentified.
- Render the bronze preview through `bash $SKILL_DIR/../../scripts/vd-dlt-preview.sh --dataset <dataset>`, never bare `python` or ad hoc installs.

## Full load

Follow `./full-load.md`.

## Destination identity

Report the resolved `workspace_id`/`lakehouse_id`.

## Pipeline artifact

The artifact is `ingestion/<name>_pipeline.Notebook/`; it runs as plain Python in the sandbox.
It holds `notebook-content.py` (the load's own code) and `.platform` (its `logicalId`), both scaffolded by `materialize-dlt-pipeline-notebook.py` (`./pipeline-notebook.md`), and is excluded from the OneLake delivery.
Its bootstrap alone is exempt from the pipeline audit's runtime-contract rule: the parameters cell reads `DOMAIN_SLUG`, the mount cell resolves the dlt project from the mounted `Files` root, and the install cell is a `%%sh` cell magic.

## Bronze preview

The wrapper resolves the Lakehouse itself, renders the dataset `--dataset` names, and skips `_dlt*` and audit tables; install nothing for it.

## Bronze tests

A pytest suite cannot reach the Lakehouse (only the brokered credential can); record a Tier 2/3 suite's execution as deferred.
