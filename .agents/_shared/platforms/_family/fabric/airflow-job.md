# The Apache Airflow Job target

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

The committed `orchestration/<Name>.ApacheAirflowJob/` a Fabric domain authors when its orchestration target is Airflow.
Data Pipeline is the default and the recommendation; Airflow is opt-in for a domain already standardised on it (ADR-0026).
Sandbox apply and run: `./airflow-job-sandbox-run.md`.

## Target and shape

- The committed `orchestration/` decides the target: a `.ApacheAirflowJob` means Airflow, a `.DataPipeline` means native, a runner `.Notebook` decides nothing.
- There is no configuration file; never invent one.
- A domain has exactly one target; the validator rejects a repo committing both, and migrating a live domain between targets is out of scope.

| Shape | Airflow | Data Pipeline |
| --- | --- | --- |
| dlt-only, dbt-only, or one dlt + one dbt | yes | yes |
| Two or more dlt workloads in one pipeline | **no**: split across items, or use Data Pipeline | yes |
| Two or more DAGs in one item | **no**: one DAG per item | n/a |
| Cadence | yes, `plugins/dag_schedules.json` | yes, `.schedules` |
| Readiness-gated and Dependency workflow types | **not yet** | yes |

Tell the user at the design stop when their shape is a **no**, and offer Data Pipeline; Generate has no authoring path for it.

## Item

```text
orchestration/<Name>.ApacheAirflowJob/
├── apacheairflowjob-content.json
├── dags/<Name>.py
├── plugins/orchestration_support.py
├── plugins/dag_schedules.json   (only when the row's Schedule is not `none`)
└── .platform
```

- `plugins/dag_schedules.json` and `.platform` are Git-only parts: committed, deployed by customer CI/CD, never carried into an ephemeral workspace (`import-airflow-job.py`'s `GIT_ONLY_PARTS`).
- **The support module goes in `plugins/`, never `dags/`.** Fabric silently discards a top-level `.py` in `dags/` that defines no DAG, and the importing DAG later fails `ModuleNotFoundError`; subdirectories under `dags/` are kept. Validator rule: `dropped-dag-module`.
- `.platform`'s `logicalId` is the item's identity: preserve it on `modify`, mint a new one only for a new item or a deliberate `recreate`.

Never hand-author the item; materialize it:

```bash
python3 $SKILL_DIR/../../scripts/platforms/_family/fabric/materialize-airflow-job.py <Name> --out orchestration \
  --domain-slug <VD_DOMAIN_SLUG> --code-lakehouse-name <VD_DOMAIN_FABRIC_LAKEHOUSE_NAME> \
  --dlt-pipeline <ingestion/<name>_pipeline.py> --dlt-runner <runner display name> \
  --dbt-notebook <the row's dbt job notebook display name> \
  --schedule '<5-field cron>'
```

- `--dlt-pipeline` and `--dbt-notebook` are each optional, at least one is required; the generator emits the chain for the legs given.
- `--schedule` writes `plugins/dag_schedules.json`; omit it for a Schedule of `none`. A malformed cron is refused.
- The materializer prints the `logicalId` and refuses to overwrite an existing item.
- `orchestration_support.py` is copied verbatim from `./templates/orchestration_support.py` and has no placeholders.

On an existing item:

- **Change a cadence** by editing `plugins/dag_schedules.json` directly, then re-run the validator. Never `recreate` for a cadence: it replaces the `logicalId` and orphans the deployed object.
- **Refresh the support module** by copying `./templates/orchestration_support.py` over the committed file and touching nothing else. An item whose DAG calls `committed_schedule()` but whose module lacks it fails `invalid-schedule-file`.

## dbt runs as its own Fabric job

- The dbt leg triggers the row's dbt job notebook `orchestration/<job>_dbt.Notebook/` (`./dbt-job-notebook.md`), exactly as a Data Pipeline activity does. Nothing runs in the Airflow worker: no dbt project in the item, no warehouse credential in the worker.
- The trigger is `MSFabricRunJobOperator` with `job_type="RunNotebook"` and `job_params` carrying only `DBT_OUTPUT_DIR = {{ run_id | run_label }}` (the filter `orchestration_support.py` registers).
- Never use `astronomer-cosmos` (it crashlooped the Fabric Celery worker) or a `BashOperator`. Validator rules: `worker-side-dbt` (Cosmos/dbt import, dbt package in requirements) and `worker-side-workload` (a `BashOperator`, or no `MSFabricRunJobOperator` at all).

## Requirements, triggerers, timeout

- `airflowRequirements` in `apacheairflowjob-content.json` is the install list, never a `requirements.txt` in `dags/`. Every entry is `==`-pinned; `apache-airflow-providers-microsoft-fabric` is the only required package.
- **A requirements change takes effect only after the job is restarted.** A `ModuleNotFoundError` on a declared package means *not restarted*, never *wrong pin*; do not change the version.
- `MSFabricRunJobOperator` defaults to `deferrable=True`, so the item must set `enableTriggerers: true` or deferred tasks never resume; the validator enforces it. Do not restate `deferrable` and do not pass `wait_for_termination`.
- Fabric's form defaults the run timeout to 10 minutes; the template sets `timeout` explicitly (`--run-timeout`, default 3600).
- Fabric's "Run Fabric Item" sample DAG hardcodes workspace and item ids; read it for operator shape only (`committed-guid` rejects it).

## What reaches the workers in a RUNNING environment

| Change | Reaches the workers? |
| --- | --- |
| A **new** file (first push of the support module; the deploy that first adds `plugins/dag_schedules.json`) | **No.** It shows on the file surface and in `getDefinition`, and the importing DAG still fails `ModuleNotFoundError`. Restart |
| An **edit** to an already-deployed DAG or `plugins/orchestration_support.py` | Yes, within about two minutes. No restart |
| `airflowRequirements` | **No.** Restart (a rebuild; minutes for the provider alone, 20+ with heavy packages) |

- **A first cadence deploy fails silently until restarted:** `committed_schedule()` returns `None` for an absent file, so the DAG runs on demand only while the repo says it is scheduled. Restart after the deploy that first adds a cadence, and confirm through the Airflow REST API (`GET /api/v1/dags/<dag id>`, `schedule_interval`), never by reading the committed file.
- `GET /api/v1/importErrors` tells "cannot import" from "never arrived"; check it before trusting the file surface.
- `environment/libraries` shows what is actually installed and `files?rootPath=` what actually reached disk; prefer them to the definition.
- The Fabric Explorer pane misreports the deployed file set in both directions; `getDefinition` is authoritative.
- Set requirements once per item. A starter pool auto-pauses when idle and a DAG triggered into it sits queued; use an always-on pool for anything iterated on.
- Restart is `POST .../environment/stop` then `.../environment/start` (both 202); poll `GET .../environment?beta=true` → `status` (`Started`, `Stopping`, `Stopped`).

## Nothing environment-specific is committed

| Value | Resolution |
| --- | --- |
| Fabric connection | A `conn_id` string only. The provider's `FabricChainedSecretBackend` (`airflow.providers.microsoft.fabric.secrets.*`) resolves a Fabric Connection GUID to a token and skips non-GUID ids so the chain handles them; prefer it to a generic Key Vault backend. The GUID reaches the DAG through an environment variable, never committed |
| Workspace id | Airflow Variable `vd_fabric_workspace_id`, set at apply time over the Airflow REST API. `airflowEnvironmentVariables` do not reach the task process and Fabric does not publish the workspace. No fallback |
| dlt runner item id | Resolved by display name in its own `resolve_dlt` task, never in an operator argument (top-level code runs on every scheduler parse). `workspace_id` and `item_id` are `template_fields`, so XCom pulls render at execution time |
| dbt job notebook item id | Resolved by display name in its own `resolve_dbt` task, for the same reason |

- The connection identity needs workspace read as well as warehouse access, because id resolution is a REST call.
- The validator rejects any literal GUID other than all-zeros, credential-shaped assignments, and connection strings.

## A dlt leg needs an `azure_key_vault` Domain

The dlt runner reads source credentials from the Domain's vault, so an item **with a dlt leg** cannot be authored on a `local_toml` Domain (`./dlt-runner-notebook.md`).
Secret Store is write-once, so the fix is a new Domain; say so early.
A dbt-only item reads no vault and is authorable on `local_toml`; do not quote the precondition for it.

## Execution model

```text
both:      resolve_dlt  →  dlt_load  →  resolve_dbt  →  dbt_build  →  record_run
                                                            ↘  workload_succeeded
dlt-only:  resolve_dlt  →  dlt_load   →  record_run / workload_succeeded
dbt-only:  resolve_dbt  →  dbt_build  →  record_run / workload_succeeded
```

- **dlt**: `MSFabricRunJobOperator` imported from `airflow.providers.microsoft.fabric.operators.run_item`, `job_type="RunNotebook"` (case-sensitive), triggering the committed runner `.Notebook`. The class is not `FabricRunItemOperator` nor `MSFabricRunItemOperator`; neither exists in this package. The runner follows `./dlt-runner-notebook.md` with its whole contract; a `.DataPipeline` target never uses it, because there the activity invokes the pipeline notebook directly.
- **dbt**: a second `MSFabricRunJobOperator` triggering the dbt job notebook with `DBT_OUTPUT_DIR`. Each leg has its own `resolve_*` task.
- **workload_succeeded**: an `EmptyOperator` leaf with the default `all_success` rule, so the DAG run state follows the workload. Never give it a trigger rule and never make `record_run` the only leaf (`recorder-only-leaf`).
- One task per workload, never one per dbt model.
- `max_active_runs=1` (no overlap).
- `schedule=committed_schedule("<dag id>")`, never a literal and never omitted: Airflow defaults a scheduleless DAG to daily (`committed-active-schedule`).
- `committed_schedule()` reads `plugins/dag_schedules.json` beside its own `__file__` and returns `None` when absent, so the same DAG is scheduled in production and on-demand in the sandbox.
- Production cadence firing is not yet live-verified: if a deployed cadence does not fire, suspect the file location first (the scheduler log names the resolved path at `INFO`), the cron second.
- Fabric's Job Scheduler cannot address an `ApacheAirflowJob` (`InvalidJobType`), so a `.schedules` file on this item does nothing.
- `invalid-schedule-file` covers malformed JSON, a bad cron, a `dag_id` no DAG declares, or a cadence no DAG reads.

## Correlation (`record_run`)

`record_run` writes one immutable JSON document per DAG run with `dag_id`, `dag_run_id`, `dbt_job_instance_id`, `dbt_invocation_id`, `dlt_job_instance_id`, `git_sha`, `status`, `failed_tasks` and timestamps, at:

```text
Files/<domain slug>/orchestration_runs/<dag id>/<dag run id>.json
```

in the code Lakehouse (`:` and `+` in the run id are replaced); the dbt project exposes the folder as the `orchestration_runs` relation.

- It must never gate the DAG: `trigger_rule="all_done"` and it swallows its own failures (`missing-record-run`, `gating-record-run`, checked per file).
- `dbt_job_instance_id` comes from the `dbt_build` task's XCom key **`run_id`**. `MSFabricRunJobOperator` pushes no `return_value`; a `return_value` pull is always `None`.
- `dbt_invocation_id` is read from `Files/<domain slug>/runs/<run label>/target/run_results.json` in the code Lakehouse.
- `status` is derived from peer task instances, never `dag_run.get_state()` (always `running` at that point).
- The mart's three runtime-audit columns are unchanged; join through `_dbt_invocation_id`.

| Airflow Variable | Purpose | Unset |
| --- | --- | --- |
| `vd_git_sha` | revision the item was deployed from | `git_sha` null, logged |
| `vd_fabric_storage_conn_id` | connection whose token carries `https://storage.azure.com/.default` | falls back to the workload connection, which may 401 on storage |

**A `token` connection triggers Fabric items but cannot reach storage:** it returns one token for every scope, so `record_run`'s OneLake write and the `run_results.json` read 401 while the run stays green.
Read the row, never a green `record_run`.
The row needs an `spn` connection or a second `token` connection minted for the storage audience, named in `vd_fabric_storage_conn_id`.

## Triggering and apply surface

Fabric's `jobs/instances` API rejects this item type (`InvalidJobType`); trigger and poll through the hosted Airflow REST API, audience `5d13f7d7-0567-429c-9880-320e9555e5fc` (the only audience it accepts).
`az` is absent in the agent container; mint through the broker (`./airflow-job-sandbox-run.md` § 4).
Applying and running belongs to `generating-orchestration`'s sandbox run, never to authoring.

| Action | API |
| --- | --- |
| Create the item | `POST /v1/workspaces/{ws}/apacheAirflowJobs` |
| Write its definition | `.../updateDefinition` |
| Deliver `transformation/`, import the dbt job notebook | `upload-to-onelake.py` + `import-notebook.sh` |
| Create the Fabric connection | `POST $BASE/api/v1/connections` (`conn_type: microsoft-fabric`) |
| Set a Variable | `POST $BASE/api/v1/variables` |
| Trigger / poll / logs | `.../dags/{dag}/dagRuns`, `.../taskInstances`, `.../logs/1?full_content=true` |
| Restart | `POST .../environment/stop` then `/start?beta=true` |
| Readiness and base URL | `GET .../environment?beta=true` → `status`, `airflowWebUrl` |
| Installed libraries | `GET .../environment/libraries?beta=true` |
| Deploy requirements only | `POST .../environment/deployRequirements?beta=true` (documented, unproven) |
| DAG files | `GET` / `PUT` / `DELETE .../files/{path}?beta=true` |

An `spn` connection's `extra` carries `auth_type: "spn"`, `tenantId`, `clientId`, `clientSecret`; the provider reads `extra`, not `login`/`password`.

## The gate

```bash
python3 $SKILL_DIR/../../scripts/platforms/_family/fabric/validate-airflow-dag.py orchestration/<Name>.ApacheAirflowJob --repo-root .
```

Exit 0 is the gate; findings print as `rule | severity | message`.
Rules: `invalid-json`, `missing-part`, `invalid-platform`, `invalid-airflow-content`, `unpinned-requirement`, `missing-required-requirement`, `embedded-secret`, `committed-connection`, `committed-guid`, `unparsable-dag`, `missing-record-run`, `gating-record-run`, `dual-orchestration-target`, `dropped-dag-module`, `worker-side-dbt`, `recorder-only-leaf`, `committed-active-schedule`, `worker-side-workload`, `misplaced-record-run`, `missing-dbt-job-notebook`, `invalid-schedule-file`.
Comments and docstrings are blanked before scanning; an unparsable DAG is reported, not passed.
On `modify`, also run `git diff HEAD -- orchestration/<Name>.ApacheAirflowJob/.platform` and halt on any `logicalId` change.
