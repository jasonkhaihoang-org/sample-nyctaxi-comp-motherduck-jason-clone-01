# Running an Apache Airflow Job in the ephemeral workspace

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

For a domain whose `orchestration/` commits a `.ApacheAirflowJob`, this replaces steps 1 to 3 of `./orchestration-running.md`: no pipeline import, no `fab job run`.
The item contract, including the restart table, is `./airflow-job.md`.
Ephemeral only; coordinates from `VD_EPHM_*`; never read or set `FAB_TOKEN*` / `VD_CREDENTIAL_*` / `AZURE_*`; on an API error report it with its request id rather than re-running.
Use `fab api` for every Fabric-API call (it is already authenticated); `az` is not installed in the agent container.

## 1. Apply the items the DAG triggers

Read the committed `dags/<Name>.py` and apply exactly what its tasks name; the Airflow Job itself is always applied.

| DAG task | Apply |
| --- | --- |
| `dlt_load` | the committed dlt runner `.Notebook` (`import-notebook.sh`, as `./orchestration-running.md` step 2) and the `ingestion/` upload |
| `dbt_build` | the `transformation/` upload (`./orchestration-sandbox-run.md` step 2, with `--prod-manifest` when `/data/cache/prod-target/manifest.json` exists) and `import-notebook.sh` for `orchestration/<job>_dbt.Notebook` |

A skipped runner import fails `resolve_dlt` with `no Notebook named '<runner>' in workspace <id>`.
Items resolve by display name at run time, so no id is rewritten: the DAG's `DBT_NOTEBOOK_NAME` and `DLT_RUNNER_NAME` must name the committed notebooks.

Apply the item with the script, which re-reads the applied definition and fails unless every committed part landed:

```bash
python3 $SKILL_DIR/../../scripts/platforms/_family/fabric/import-airflow-job.py <Name> \
  orchestration/<Name>.ApacheAirflowJob --workspace-id "$WS"
```

<!-- not-a-runnable-fence: status, stop and start are three separate calls -->
```bash
fab api "workspaces/$WS/apacheAirflowJobs/$ITEM/environment?beta=true"            # status
fab api "workspaces/$WS/apacheAirflowJobs/$ITEM/environment/stop?beta=true"  -X post
fab api "workspaces/$WS/apacheAirflowJobs/$ITEM/environment/start?beta=true" -X post
```

Upload `ingestion/` only for a DAG with `dlt_load`:

```bash
python3 $SKILL_DIR/../../scripts/platforms/_family/fabric/upload-to-onelake.py --source ingestion \
  --workspace-id "$WS" --lakehouse-id <ephemeral paired lakehouse id> [--warehouse-id <warehouse>] \
  --domain-slug <slug> --subdir ingestion
```

`--source` is the `ingestion` folder, never the repository root (the script refuses a root).
A missing upload fails `dlt_load` with only "the Fabric item run failed", and a mis-rooted one as `System_Cancelled_Session_Statements_Failed`; neither names a path.

## 2. Inject the workspace id

Set the Airflow Variable `vd_fabric_workspace_id` to the ephemeral workspace id with the step 4 token (not `fab api`):

```bash
# POST $BASE/api/v1/variables   {"key": "vd_fabric_workspace_id", "value": "<ephemeral ws id>"}
```

`airflowEnvironmentVariables` do not reach the task process; a Variable takes effect immediately.
Without it every run fails in the `resolve_*` task.

## 3. Restart after adding a file or changing `airflowRequirements`

A new file or a requirements change needs `stop`/`start` and a `Started` status before triggering; an edit to an already-deployed file reaches the workers in about two minutes with no restart.
A `ModuleNotFoundError` on a module the item plainly carries means *not restarted*, never *wrong pin*; do not edit the version.
`GET /api/v1/importErrors` tells "cannot import" from "never arrived"; `files?rootPath=` will confirm a file the workers cannot see.
The Fabric Explorer pane misreports deployed files both ways; `getDefinition` is authoritative.

## 4. Mint the Airflow token, then create the connections

```python
from vibedata_studio_azure_cred_broker import StudioAzureCredBroker
AIRFLOW = "5d13f7d7-0567-429c-9880-320e9555e5fc"          # the Airflow service audience
token = StudioAzureCredBroker(audience_map={AIRFLOW: "fabric_airflow"}) \
    .get_token(f"{AIRFLOW}/.default").token
```

The `audience_map` override is required: the broker's default audiences do not include this one, and the Airflow API accepts no other.
The same token authenticates every Airflow-service call on this page.

Create `fabric_default` before the first trigger with `POST $BASE/api/v1/connections`; every task authenticates through it, so a missing or malformed one fails `resolve_dlt` at once:

| Field | Value |
| --- | --- |
| `connection_id` | `fabric_default` (the API rejects `conn_id`) |
| `conn_type` | `microsoft-fabric` |
| `extra` | a **JSON-encoded string**, not a nested object, holding `auth_type: token`, `accessToken`, `expiresAt`; both token fields are required |

This connection handles no secret and drives the whole workload, but 401s on storage, so `record_run` leaves no row.
For the row, create a second connection the same way with a broker token for `https://storage.azure.com/.default`, and name it in the `vd_fabric_storage_conn_id` Variable.
That path is not yet live-verified: until it is, a missing row on a green run is expected; record the gap in the evidence.

## 5. Trigger and wait

Trigger and poll through the hosted Airflow REST API (`dagRuns`, `taskInstances`, `.../logs/1?full_content=true`) with the step 4 token; Fabric's `jobs/instances` returns `InvalidJobType` and `apacheAirflowJobs/{id}/dagRuns` is `EntityNotFound`.
Never use a schedule to make a run happen: the import carries no `plugins/dag_schedules.json`, and a literal schedule fails `committed-active-schedule`.

A dlt + dbt run takes 10–20 minutes.
Launch a blocking wait with `start_async_bash` and `timeout_seconds: 1800` (default 300), then `wait_for_async_bash` with `wait_timeout_seconds: 300`.
`running` means the local command is live; `timed_out` means it was killed.
Never trigger a second run for the same change; read the DAG run and its task instances instead.

## The gate

The DAG run reaches terminal success with **every task instance green**, plus the dbt `run_results.json` evidence, recorded in the Plan's `## Execution evidence`.
Read `taskInstances`, not only the run state: `record_run` never fails, so a green run over a failed `dlt_load` is possible.
An apply with no run, or static validation, is not evidence.
Never activate a schedule.
