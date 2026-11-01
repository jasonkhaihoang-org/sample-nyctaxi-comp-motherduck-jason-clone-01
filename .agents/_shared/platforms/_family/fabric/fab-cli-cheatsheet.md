# `fab` CLI cheatsheet — out-of-flow debugging

`fab` is installed in the intent runtime. This page is for **out-of-flow debugging only**; flow steps carry their own commands.

## Auth — do NOT manage manually

`fab` resolves to the **vdfab shim**, which mints `FAB_TOKEN` and `FAB_TOKEN_ONELAKE` per call; never inspect or set them.
Azure-resource commands (capacities, `fab api -A azure`) are unavailable to the agent.
**On 401, ask the user to re-login to Studio.**

## Common debug commands

The recipes name a `fabric_lakehouse` Intent's coordinates. Each `<VD_...>` is a setting of this Intent, not a shell variable: substitute its value. On a `fabric_warehouse` Intent use `VD_EPHM_FABRIC_WAREHOUSE_WORKSPACE_NAME` for the workspace, and reach its items as `<name>.DataWarehouse` — a Warehouse has no `Tables` filesystem path, so inspect its tables over TDS (the dbt sandbox target) rather than through `fab ls`.

| Need | Command |
| --- | --- |
| Confirm auth + see your identity | `fab whoami` |
| List workspaces accessible to you | `fab ls` |
| List items in a workspace | `fab ls "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace"` |
| List items with IDs (long form) | `fab ls "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace" -l` |
| List Lakehouse tables | `fab ls "/<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace/<VD_EPHM_FABRIC_LAKEHOUSE_NAME>.Lakehouse/Tables"` |
| Read an item's metadata | `fab get "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace/<name>.<type>"` |
| Read a notebook back from Fabric (e.g. to compare with local) | `fab export "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace/<name>.Notebook" -o /tmp/nb` |
| List a pipeline's recent runs (discover run ids) | `fab job run-list "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace/<pipeline>.DataPipeline"` |
| Inspect one pipeline run's status and failure reason | `fab job run-status "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace/<pipeline>.DataPipeline" --id <id>` |
| Navigate by path (interactive shell) | `fab cd "<VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME>.Workspace"` then `fab ls`, `fab pwd` |

`<type>` is the Fabric item kind: `Notebook`, `DataPipeline`, `Lakehouse`, etc.

## What this is NOT for

- **Deploying / running orchestration** — compose the single-capability Fabric scripts in `scripts/platforms/_family/fabric/` (`upload-to-onelake.py`, `import-notebook.sh`, `prepare-ephemeral-import.py`, `import-pipeline.sh`, `run-item.sh`, `export-item.sh`, `validate-datapipeline.py`, `materialize-runner.py`, `get-dbt-job-evidence.py`). `./orchestration-sandbox-run.md` is an example composition.
- **Deleting items as a recovery step**: manual `fab rm` risks orphaning git artifacts.
