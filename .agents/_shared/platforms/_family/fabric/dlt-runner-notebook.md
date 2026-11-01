# The dlt runner notebook

The committed `orchestration/<runner>.Notebook/` that fetches a dlt pipeline's code from OneLake and runs it inside Fabric.
Step 1 of `./orchestration-authoring.md` materializes it with `../../../../scripts/platforms/_family/fabric/materialize-runner.py --engine dlt --platform <lakehouse|warehouse>`.

**A `.DataPipeline` target has no runner on either Fabric platform.** Its pipeline is its own notebook, `ingestion/<name>_pipeline.Notebook/`, invoked directly by the activity.
The runner exists only for an `.ApacheAirflowJob` target, whose DAG task names a deployed notebook.
The item shape, the `.platform` `logicalId`, the flat `notebookId`/`workspaceId` reference and the validator's rules are the same for both item kinds.

## What the runner does

A Fabric **Python** notebook (`jupyter_python`, no Spark). At run time it:

1. checks that a default Lakehouse is attached and lives in this workspace;
2. copies `/lakehouse/default/Files/<DOMAIN_SLUG>/ingestion` into a private local directory;
3. installs its execution unit, then `requirements.txt` and each vendored connector's, and runs the named pipeline.

- Never embed pipeline code in the runner; it reads the code through OneLake.
- The destination comes from the committed destination table (`[destination.filesystem]` on a Lakehouse Domain, `[destination.fabric]` on a Warehouse one). The runner refuses a config naming another workspace, so an un-retargeted copy fails loudly.

## The attachment is the code path

- The deployer binds the default Lakehouse attachment per workspace; nothing about it is committed.
- Both first-cell checks catch silent failures: no attachment means no `/lakehouse/default`; an attachment in **another** workspace mounts that workspace's `Files/` and runs another Domain's code green.
- Never export a runner back out of Fabric: the export commits the workspace's attachment ids. Import the committed directory with `import-notebook.sh <name> orchestration/<runner>.Notebook`, which updates an existing item in place.

## The leg needs an `azure_key_vault` Domain, on both platforms

`local_toml` credentials live in the agent container's operator store, the runner executes on Fabric compute, and `upload-to-onelake.py` ships only tracked files, so the credentials never reach Fabric.
Never upload `secrets.toml` and never pass secrets as parameters.
On a `local_toml` Domain the pipeline carries dbt activities only and the dlt load stays a sandbox run; the fix is a new `azure_key_vault` Domain, because a Domain's Secret Store is write-once. Say so early.
The vault URL is not a parameter: the provider reads `[providers.azure_key_vault] vault_url` from the committed config.

## Lakehouse vs Warehouse — the complete difference

| | `fabric_lakehouse` | `fabric_warehouse` |
| --- | --- | --- |
| Template | `./templates/dlt-notebook-runner-lakehouse.py` | `./templates/dlt-notebook-runner-warehouse.py` |
| Committed destination table | `[destination.filesystem]` | `[destination.fabric]` |
| Attached Lakehouse | the Domain's own Lakehouse | the Intent's **Ephemeral Paired Lakehouse** (a Warehouse has no `Files/` area) |
| Upload flag | `--lakehouse-id` = `VD_EPHM_FABRIC_LAKEHOUSE_ID` | `--lakehouse-id` = `VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID`, `--warehouse-id` = `VD_EPHM_FABRIC_WAREHOUSE_ID` |
| What the upload retargets | `workspace_id`, `lakehouse_id`, `bucket_url` (that Lakehouse's `Tables` folder) | `workspace_id`, `warehouse_id`, `bridge_lakehouse_id` where the table commits one, and a committed staging `bucket_url` (the Ephemeral Paired Lakehouse's `Files/staging` folder) |
| Where the load lands | the Lakehouse's Delta tables | the Warehouse, via Parquet staging and `COPY INTO` |
| Where the load runs | this notebook's kernel | a child interpreter |

### The Warehouse child interpreter

- The Fabric kernel imports `adlfs` before the first cell and keeps it cached; dlt staging needs the newer one `pip` installs, which only a fresh process sees.
- The child imports `notebookutils`, mints its own tokens and reads Key Vault, so it is handed no credentials.
- The child bootstrap registers the notebook Key Vault provider.
- It supplies the staging **credential** only; dlt reads the staging `bucket_url` from `[destination.filesystem]`, which the upload retargets to the run's own Lakehouse so an Intent never stages into the Domain's Paired Lakehouse, and with no such table the load is row by row.
- It treats a trailing-slash directory `HEAD` on OneLake as "not a blob", because OneLake answers it `403 AuthenticationFailed` for a notebook-minted token.
- `notebookutils.credentials.getToken` mints every audience needed (SQL, OneLake, Fabric REST, Key Vault).

A Lakehouse load runs in the kernel; on the Python 3.12 kernel Fabric's OneLake filesystem signs in as the notebook, so that leg carries no credential.

A first Warehouse run installs the pipeline's own `requirements.txt` (the kernel has no connector dependencies).
A dataset already holding `_dlt_pipeline_state` from a sandbox load restores incremental cursors and loads nothing new; a genuine full load shows in `audit_runs` as `first_run` true with nonzero `total_rows_extracted`.

## One template per platform

`--platform` selects the template file; the runner never branches at run time.
Shared invariants (parameter contract, attachment checks, code copy, retarget refusal) are asserted against **both** templates in `../../../../scripts/platforms/_family/fabric/__tests__/test_materialize_runner.py`; add a shared invariant there.

## Parameters — exactly two

Each in the activity's `typeProperties.parameters` as `{"value": …, "type": "string"}`:

| Parameter | Value | Note |
| --- | --- | --- |
| `DOMAIN_SLUG` | the value of `VD_DOMAIN_SLUG` | names the folder under the attached Lakehouse's `Files/` |
| `PIPELINE` | the invoked `ingestion/<name>_pipeline.py` filename | must name a committed pipeline |

**Values are literals, written out.** Fabric passes a parameter through verbatim, so a committed variable reference (the setting's name instead of its value) arrives as that text and the run dies with `System_Cancelled_Session_Statements_Failed`.
Take the value of the named setting and commit the string; it is identical in every workspace.

- The activity references the notebook through flat `typeProperties.notebookId` / `typeProperties.workspaceId`.
- No workspace, Lakehouse or Warehouse id or name, and no correlation parameter; a dlt run adds no schema, audit table or product column.
- `materialize-runner.py` prints the item's `logicalId`, needs no ephemeral workspace and no `fab`. There is no seeded `infra/dbt|dlt/*_notebook_runner.ipynb`; this template is the only runner.

## How the code gets there

`upload-to-onelake.py` delivers the tracked contents of `ingestion/` to `Files/<slug>/ingestion/` in the attached Lakehouse:

- it deletes the destination folder first (the runner reads the folder, so a deleted pipeline would otherwise stay importable), after reading and retargeting every byte, so a failed delivery leaves the working one;
- it writes `revision.txt` naming the commit, last; one copy, no history;
- it omits deletions and untracked files, rejects secret filenames, runtime artifacts and symlinks, bounds file count and size, and retargets the uploaded `.dlt/config.toml` only;
- nothing serialises two concurrent deliveries to the same folder.

## What `validate-datapipeline.py` rejects

- a required parameter missing, or a forbidden one present (`WORKSPACE_ID`, `WORKSPACE_NAME`, `LAKEHOUSE_ID`, `LAKEHOUSE_NAME`, `WAREHOUSE_ID`, `WAREHOUSE_NAME`);
- an unexpanded value (a setting's name used as a variable, `$(…)`, `${…}`, `@pipeline().…`);
- `notebookId` absent, or `workspaceId` not the all-zeros GUID;
- Synapse-shaped `notebook` / `notebookReference` / `linkedServiceName` keys, which make Fabric refuse the document with `'NotebookId' cannot be null`;
- `PIPELINE` not naming a committed `ingestion/<name>_pipeline.py`.
