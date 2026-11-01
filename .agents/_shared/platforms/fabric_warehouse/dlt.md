# dlt on a Fabric Warehouse

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

## Authoring

- The pipeline is a Fabric notebook item, not a script: scaffold it with `./pipeline-notebook.md` § Generate instead of writing `ingestion/<name>_pipeline.py`. The rest of the layout (`sources/`, `requirements.txt`) is unchanged.
- The destination literal is `"fabric"`.
- A notebook is executed, never imported: the load runs flat in its own cell, so validate its entry point by reading the file, not importing it.

## Destination

`fabric`. Recommended auth method `fabric_token`, Vibedata's custom token auth: the sandbox signs in through Studio's broker, a Fabric notebook as its own identity. Introspect with `--activate vibedata.dlt.fabric_warehouse._patch:apply`.

| Key | Value |
| --- | --- |
| `workspace_id` | `<VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_ID>` |
| `warehouse_id` | `<VD_DOMAIN_FABRIC_WAREHOUSE_ID>` |
| `credentials.host` | `<VD_DOMAIN_FABRIC_WAREHOUSE_SQL_ENDPOINT>` |
| `credentials.database` | `<VD_DOMAIN_FABRIC_WAREHOUSE_NAME>` |

Then write the bulk-staging location the Paired Lakehouse gives, per `./config-staging-section.md`; the user is not asked for it.

## Sandbox run

- Runtime distribution: `vibedata-dlt-fabric-warehouse-studio` (import `vibedata.dlt.fabric_warehouse`). Dialect: `destination="fabric"`, `staging=onelake_staging()`, plain `pipeline.run(source)`.
- The load has two legs inside one run: Parquet staged into the Intent's Ephemeral Paired Lakehouse `Files/` (`onelake_staging()` resolves the location dlt was configured with, which Studio overrides per Intent), then `COPY INTO` the ephemeral Warehouse. `finalize()` audits the run.
- Never inspect, set or edit `FAB_TOKEN*`, `AZURE_CLIENT_ID` or the broker env; the unit mints its own audience-bound token. An auth failure means the user must re-login to Studio.
- Secrets resolve from the Domain's Secret Store, connection-keyed; the pipeline file names no store, secret or staging location. The committed config carries what `## Provider config` in `../../secret-stores/<secret-store>.md` gives and, for a Domain with a Paired Lakehouse, `[destination.filesystem] bucket_url`.
- Loaded tables land in the ephemeral Warehouse under the dataset schema; nothing appears on the container filesystem. Confirm them with `lakehouse_schema` / `lakehouse_query` (which serve a Warehouse too). `lakehouse_query` does not filter statements, so send only reads, and never use it in place of the rendered preview.
- Render the bronze preview through `bash $SKILL_DIR/../../scripts/vd-dlt-preview.sh --dataset <dataset>`, never bare `python` or ad hoc installs.

**Never import the pipeline module to check it.** The template runs at module scope, so an import calls `setup_environment()` and `pipeline.run()`: a real load that looks like a hang, and killing it leaves a partial load. Use the run command once.

Ingestion is complete only with a load package and the rendered preview; a committed file or a successful import is neither. Without both, say what is missing and stop.

## Full load

The Warehouse loads from this container, so the full load runs here: the sample-load command without `DLT_INGEST_LIMIT=<N>`, staging through the bridge into the ephemeral Warehouse as the sample did, then the landing gates. It loads every resource the pipeline names, as committed. Run it once, after the pipeline and its docs are final: its gate verdicts are the evidence, so never run it again to confirm a count.

## Destination identity

Report the resolved `workspace_id`/`warehouse_id`.

## Pipeline artifact

The artifact is `ingestion/<name>_pipeline.Notebook/`; it runs as plain Python in the sandbox.
It holds `notebook-content.py` (the load's own code) and `.platform` (its `logicalId`), both scaffolded by `materialize-dlt-pipeline-notebook.py` (`./pipeline-notebook.md`), and is excluded from the OneLake delivery.
Its bootstrap alone is exempt from the pipeline audit's runtime-contract rule: the parameters cell reads `DOMAIN_SLUG`, the mount cell resolves the dlt project from the mounted `Files` root, and the install cell is a `%%sh` cell magic.

## Bronze preview

The wrapper queries the ephemeral Warehouse over TDS, rendering the schema `--dataset` names and skipping `_dlt*` and audit tables.

## Bronze tests

A pytest suite cannot reach the Warehouse (only the brokered token can); record a Tier 2/3 suite's execution as deferred.
