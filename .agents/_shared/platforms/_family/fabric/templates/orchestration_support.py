"""Runtime helpers for a Fabric Apache Airflow Job DAG.

Contract: docs/design/orchestration/fabric/airflow-job.md

Nothing here accepts a committed workspace id, item id, or credential. The
workspace is injected at apply time as an Airflow Variable, the dlt and dbt
runner notebooks are resolved by display name, and credentials resolve
through the Airflow connection named by VD_FABRIC_CONN_ID.

Copied verbatim into every materialized item — it carries no placeholders,
because every value it needs is resolved at run time.

Lives in the item's plugins/ folder, NOT dags/: Fabric silently discards a
top-level .py in dags/ that defines no DAG, and Airflow puts plugins/ on
sys.path (both verified live, VD-5578).
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

ORCHESTRATION_RUNS_TABLE = "orchestration_runs"
FABRIC_API_HOST = "https://api.fabric.microsoft.com"
FABRIC_API_SCOPE = "https://api.fabric.microsoft.com/.default"
ONELAKE_BLOB_HOST = "https://onelake.blob.fabric.microsoft.com"
ONELAKE_SCOPE = "https://storage.azure.com/.default"
# Cadence lives beside this module, never inside the DAG. See committed_schedule().
SCHEDULES_FILE = "dag_schedules.json"
RECORD_RUN_TASK_ID = "record_run"
DLT_TASK_ID = "dlt_load"
DBT_TASK_ID = "dbt_build"

# MSFabricRunJobOperator pushes NO return_value. It pushes discrete XCom keys —
# run_id, item_id, item_name, item_type, run_status (and run_link for a
# notebook) — and the Fabric job instance id is run_id. Pulling "return_value"
# returns None on every run and silently empties the fields this relation exists
# to carry; run-verified against a fully green run (VD-5578), which is the only
# kind of run that can expose it.
JOB_INSTANCE_XCOM_KEY = "run_id"


WORKSPACE_ID_VAR = "vd_fabric_workspace_id"
# Provenance and the storage identity, both per-environment and both set the same
# way the workspace id is — an Airflow Variable, because the item's
# airflowEnvironmentVariables were verified NOT to reach the worker's task
# process (see current_workspace_id).
GIT_SHA_VAR = "vd_git_sha"
STORAGE_CONN_ID_VAR = "vd_fabric_storage_conn_id"


def current_workspace_id():
    """The workspace this Airflow Job runs in, from an Airflow Variable.

    Fabric publishes no workspace id to the DAG at all — verified live by dumping
    the whole environment: the only FABRIC_* entries are the secret backend's URL
    and scope, AZURE_CLIENT_ID is all zeros, and AZURE_TENANT_ID is Fabric's own
    service tenant. The item's `airflowEnvironmentVariables` were also verified
    NOT to reach the worker's task process, so that route is unavailable.

    An Airflow Variable is the remaining mechanism, and the better one: it is
    stored in the Airflow metadata DB, so the apply step can set it over the
    Airflow REST API and it takes effect immediately — where a requirements or
    environment change costs a full rebuild measured in tens of minutes.

    Set per environment, never committed. There is deliberately no fallback: a
    wrong workspace id would run the DAG against someone else's data rather than
    fail.
    """
    from airflow.models import Variable

    workspace_id = Variable.get(WORKSPACE_ID_VAR, default_var=None)
    if not workspace_id:
        raise RuntimeError(
            f"Airflow Variable {WORKSPACE_ID_VAR!r} is not set; the apply step must set it "
            "to the target workspace id (Admin > Variables, or the Airflow REST API). "
            "The DAG must not guess one."
        )
    return workspace_id


def resolve_item_id(display_name, item_type="Notebook", conn_id=None):
    """Resolve a committed item's id by display name, over the Fabric REST API.

    Name-indirection is what lets one committed DAG serve every workspace: the
    runner's name is a Domain coordinate, its id is not.

    The provider offers no name-to-id lookup of its own — its only item helper
    resolves the other direction, id to name — so this calls the list endpoint
    directly, borrowing the provider connection purely for the access token.
    """
    import requests
    from airflow.providers.microsoft.fabric.hooks.connection.rest_connection import (
        MSFabricRestConnection,
    )

    connection = MSFabricRestConnection(
        conn_id=conn_id or os.environ.get("VD_FABRIC_CONN_ID", "fabric_default")
    )
    headers = connection.get_headers(FABRIC_API_SCOPE)
    workspace_id = current_workspace_id()

    response = requests.get(
        f"{FABRIC_API_HOST}/v1/workspaces/{workspace_id}/items",
        params={"type": item_type},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()

    matches = [
        item for item in response.json().get("value", [])
        if item.get("displayName") == display_name
    ]
    if not matches:
        raise RuntimeError(
            f"no {item_type} named {display_name!r} in workspace {workspace_id}; "
            "the committed DAG references an item this workspace does not hold"
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"{len(matches)} items named {display_name!r} in workspace {workspace_id}; "
            "the name must be unique for id resolution to be deterministic"
        )
    return matches[0]["id"]


def committed_schedule(dag_id):
    """This DAG's committed cadence, or None when the deployment carries none.

    The cadence is a Git-only part, exactly as `.schedules` is on the Data
    Pipeline target: customer CI/CD deploys `plugins/dag_schedules.json` with the
    rest of the item, and `import-airflow-job.py` never carries it into an
    ephemeral workspace. So the SAME committed DAG runs to a real cadence in
    production and on-demand-only in the sandbox, and an ephemeral item cannot
    fire on its own after the intent ends — not by a rule someone can edit, but
    because the file naming the cadence is not there (VD-5767).

    The native route is unavailable: Fabric's Job Scheduler cannot address an
    ApacheAirflowJob at all, returning InvalidJobType for every job type, so a
    `.schedules` file on this item has nothing to name (probed live, VD-5767).

    ABSENT is the sandbox, and returns None. PRESENT BUT BROKEN is a deployment
    defect and raises: a malformed file that degraded to None would silently turn
    the daily 06:00 run the user asked for into on-demand-only, with nothing
    anywhere saying so. This runs on every scheduler parse, so the failure
    surfaces as a DAG import error, which is the loudest channel there is.

    Absence is logged with the path it resolved to. The sandbox, a first cadence
    deploy the job has not been restarted for, and a plugins/ folder Fabric
    mounted somewhere other than beside this module all look the same from here
    — an absent file — and the resolved path in the scheduler log is the one
    piece of evidence that tells them apart.
    """
    path = Path(__file__).resolve().parent / SCHEDULES_FILE
    if not path.is_file():
        log.info("cadence file %s is absent, so DAG %r has no committed cadence and runs on "
                 "demand only: this is the sandbox, or a first cadence deploy the job has not "
                 "been restarted for", path, dag_id)
        return None
    schedules = json.loads(path.read_text())
    if not isinstance(schedules, dict):
        raise ValueError(f"{SCHEDULES_FILE} must be an object mapping dag_id to a cron "
                         f"expression, got {type(schedules).__name__}")
    cron = schedules.get(dag_id)
    if cron is None:
        return None
    if not isinstance(cron, str) or not cron.strip():
        raise ValueError(f"{SCHEDULES_FILE}[{dag_id!r}] must be a non-empty cron string, "
                         f"got {cron!r}")
    return cron


def deployed_git_sha():
    """The commit this deployed item was built from, or None.

    Read from an Airflow Variable, for the reason current_workspace_id() records:
    the item's `airflowEnvironmentVariables` were verified NOT to reach the
    worker's task process. The previous implementation read `VD_GIT_SHA` from the
    environment, so it could never have been populated by any route — the field
    was not merely unset, it was unsettable, and it was null on every run
    (VD-5578, VD-5767).

    Unlike the workspace id this never raises and falls back to None: provenance
    is evidence, and a missing SHA must not fail a workload that otherwise
    succeeded. It is logged, so an absent one is visible rather than silently
    null in the run record.

    Customer CI/CD sets it at deploy, beside `vd_fabric_workspace_id`.
    """
    from airflow.models import Variable

    sha = Variable.get(GIT_SHA_VAR, default_var=None)
    if not sha:
        log.warning(
            "Airflow Variable %r is not set, so this run records no commit; the deploy "
            "step sets it to the revision the item was built from", GIT_SHA_VAR)
        return None
    return sha


def storage_connection_id(conn_id=None):
    """The connection used for OneLake reads and writes.

    Separate from the workload connection because a `token`-type connection
    returns its ONE token for every scope: an agent-built sandbox connection
    holding a Fabric-API token drives the whole workload but 401s on storage, so
    `record_run`'s write and the `run_results.json` read both fail and a fully
    green run leaves no correlation row at all (run-verified, VD-5578).

    Point `vd_fabric_storage_conn_id` at a connection whose token carries the
    storage audience — an `spn` connection, or a second `token` one the apply
    step mints for `https://storage.azure.com/.default` — and the row lands on an
    ordinary run. Unset, this falls back to the workload connection, which is the
    previous behaviour.
    """
    from airflow.models import Variable

    return Variable.get(STORAGE_CONN_ID_VAR, default_var=None) or conn_id


def run_label(run_id):
    """This DAG run's output folder name under the dbt job's runs/.

    A dag_run_id carries `:` and `+` (and a manual one anything at all), and the folder
    is one path segment of [A-Za-z0-9_.-]. The DAG passes this to the dbt job notebook as
    DBT_OUTPUT_DIR and the recorder reads the same folder back, so both call this one function.
    """
    return re.sub(r"[^A-Za-z0-9_.-]", "-", str(run_id))[:255]


def resolve_runner_coordinates(display_name, item_type="Notebook", conn_id=None, **_):
    """Resolve the runner's workspace and item id, as a task.

    Returned through XCom so the operator's templated `workspace_id` and
    `item_id` render at execution time. Calling `resolve_item_id` directly in an
    operator argument would run it on every scheduler parse loop instead, and
    would turn a missing workspace id into a DAG import error rather than a task
    failure.
    """
    return {
        "workspace_id": current_workspace_id(),
        "item_id": resolve_item_id(display_name, item_type=item_type, conn_id=conn_id),
    }


def write_orchestration_run(conn_id=None, code_lakehouse_name=None, domain_slug=None,
                            **context):
    """Write one orchestration_runs row correlating this DAG run to its workloads.

    Evidence, never a gate: this task carries an all-done trigger rule and this
    function swallows its own failures, so a recording problem can never turn a
    successful workload into a failed run.
    """
    try:
        task_instance = context["ti"]
        dag_run = context["dag_run"]
        # Both OneLake calls below need the storage audience, which the workload
        # connection may not carry; resolved once so the row and the invocation id
        # cannot disagree about which identity read them.
        storage_conn_id = storage_connection_id(conn_id)

        dbt_job_instance_id = task_instance.xcom_pull(
            task_ids=DBT_TASK_ID, key=JOB_INSTANCE_XCOM_KEY)
        log.info("correlating dag_run=%s dlt_job=%s dbt_job=%s",
                 dag_run.run_id,
                 task_instance.xcom_pull(task_ids=DLT_TASK_ID, key=JOB_INSTANCE_XCOM_KEY),
                 dbt_job_instance_id)
        row = {
            "dag_id": dag_run.dag_id,
            "dag_run_id": dag_run.run_id,
            "dbt_job_instance_id": dbt_job_instance_id,
            "dbt_invocation_id": _dbt_invocation_id(
                dbt_job_instance_id, run_label(dag_run.run_id), code_lakehouse_name=code_lakehouse_name,
                domain_slug=domain_slug, conn_id=storage_conn_id),
            "dlt_job_instance_id": task_instance.xcom_pull(
                task_ids=DLT_TASK_ID, key=JOB_INSTANCE_XCOM_KEY),
            "git_sha": deployed_git_sha(),
            "status": _workload_status(dag_run),
            "failed_tasks": _failed_task_ids(dag_run),
            "started_at": dag_run.start_date,
            "ended_at": datetime.now(timezone.utc),
        }
        _insert_run_row(row, code_lakehouse_name=code_lakehouse_name,
                        domain_slug=domain_slug, conn_id=storage_conn_id)
        log.info("recorded orchestration run %s", row["dag_run_id"])
    except Exception:
        log.exception(
            "failed to record the orchestration run; the workload result is unaffected. "
            "A 401 here is usually the storage audience: a `token` connection returns its "
            "one token for every scope, so point Airflow Variable %r at a connection whose "
            "token carries https://storage.azure.com/.default", STORAGE_CONN_ID_VAR
        )


def _dbt_invocation_id(job_instance_id, label, code_lakehouse_name=None, domain_slug=None, conn_id=None):
    """dbt's own invocation id, read from the dbt job notebook's output.

    dbt runs as its own Fabric job here — the row's dbt job notebook — not in the
    Airflow worker, so there is no local target/ to read. The DAG names the run's
    output folder by `label` (run_label of this DAG run), so dbt writes
    target/run_results.json under Files/<domain slug>/runs/<label>/ in the code
    Lakehouse and no other run can overwrite it.

    The invocation id is the join key every mart already stamps as
    _dbt_invocation_id, so the row carries it alongside the job instance id
    rather than instead of it. A failure here returns None and is logged: this
    is evidence, and the caller must not fail the run over it.
    """
    if not job_instance_id or not code_lakehouse_name or not domain_slug:
        log.warning("dbt leg job instance or code location unavailable; invocation id not recorded")
        return None

    import requests
    from airflow.providers.microsoft.fabric.hooks.connection.rest_connection import (
        MSFabricRestConnection,
    )

    connection = MSFabricRestConnection(
        conn_id=conn_id or os.environ.get("VD_FABRIC_CONN_ID", "fabric_default")
    )
    try:
        lakehouse_id = resolve_item_id(code_lakehouse_name, item_type="Lakehouse", conn_id=conn_id)
        url = (
            f"{ONELAKE_BLOB_HOST}/{current_workspace_id()}/{lakehouse_id}"
            f"/Files/{domain_slug}/runs/{label}/target/run_results.json"
        )
        response = requests.get(
            url, headers=connection.get_headers(ONELAKE_SCOPE), timeout=60
        )
        response.raise_for_status()
        return response.json().get("metadata", {}).get("invocation_id")
    except Exception:  # noqa: BLE001 — evidence, never a gate
        log.warning("could not read the dbt job's run_results.json for job instance %s",
                    job_instance_id)
        return None


def _peer_task_instances(dag_run):
    """Every task instance in this run except the recorder itself."""
    return [ti for ti in dag_run.get_task_instances()
            if ti.task_id != RECORD_RUN_TASK_ID]


def _failed_task_ids(dag_run):
    return sorted(ti.task_id for ti in _peer_task_instances(dag_run)
                  if ti.state in ("failed", "upstream_failed"))


def _workload_status(dag_run):
    """The workload's outcome, derived from its peers.

    `dag_run.get_state()` is read while this task is still executing, so it is
    always "running" and records nothing. The workload's real outcome is whether
    any non-recorder task failed.
    """
    peers = _peer_task_instances(dag_run)
    if not peers:
        return "unknown"
    if any(ti.state in ("failed", "upstream_failed") for ti in peers):
        return "failed"
    if all(ti.state in ("success", "skipped") for ti in peers):
        return "success"
    return "partial"


def _run_blob_name(dag_run_id):
    """A dag_run_id contains `:` and `+`, which do not belong in a blob path."""
    return re.sub(r"[^A-Za-z0-9._-]", "-", dag_run_id) + ".json"


def _insert_run_row(row, code_lakehouse_name=None, domain_slug=None, conn_id=None):
    """Append the run as one JSON document in OneLake, for dbt to expose.

    Deliberately NOT a TDS insert from the worker. Nothing else on this target
    executes in the Airflow worker — that is the whole reason Cosmos was dropped
    — and a direct warehouse write would put a SQL driver and a warehouse
    credential back in it, for one row. The worker already holds a storage token
    and already reads the dbt job's own run output through it, so this reuses a
    path that is proven rather than opening a second one.

    One immutable document per DAG run, at

        Files/<domain slug>/orchestration_runs/<dag id>/<dag run id>.json

    in the code Lakehouse — the same Lakehouse the runners read their code
    from, named by the DAG rather than resolved from a committed id. The domain's
    dbt project exposes that folder as the `orchestration_runs` relation; a mart
    joins to it on `dbt_invocation_id`, which every mart already stamps.
    """
    if not code_lakehouse_name or not domain_slug:
        raise RuntimeError(
            "record_run needs code_lakehouse_name and domain_slug to place the row; "
            "the DAG passes both as op_kwargs"
        )

    import requests
    from airflow.providers.microsoft.fabric.hooks.connection.rest_connection import (
        MSFabricRestConnection,
    )

    workspace_id = current_workspace_id()
    lakehouse_id = resolve_item_id(code_lakehouse_name, item_type="Lakehouse", conn_id=conn_id)
    connection = MSFabricRestConnection(
        conn_id=conn_id or os.environ.get("VD_FABRIC_CONN_ID", "fabric_default")
    )
    url = (
        f"{ONELAKE_BLOB_HOST}/{workspace_id}/{lakehouse_id}/Files/{domain_slug}"
        f"/{ORCHESTRATION_RUNS_TABLE}/{row['dag_id']}/{_run_blob_name(row['dag_run_id'])}"
    )
    headers = {
        **connection.get_headers(ONELAKE_SCOPE),
        "x-ms-blob-type": "BlockBlob",
        "Content-Type": "application/json",
    }
    # default=str renders the timestamps; they are datetimes, not strings.
    body = json.dumps(row, default=str, indent=1).encode()
    response = requests.put(url, data=body, headers=headers, timeout=60)
    response.raise_for_status()
    log.info("wrote %s", url)
