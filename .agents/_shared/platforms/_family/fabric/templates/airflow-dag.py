"""Orchestration DAG for @@NAME@@ — authored by Build, deployed by customer CI/CD.

Contract: docs/design/orchestration/fabric/airflow-job.md

No workspace id, item id, or credential is committed here. The workspace is
injected at apply time as an Airflow Variable; the dlt runner and the dbt job
notebooks are resolved by display name over the Fabric REST API; every credential resolves
through the Airflow connection named by FABRIC_CONN_ID.

Each workload runs as its own Fabric job — the same notebooks the Data Pipeline
target invokes, with the same parameters. Airflow only triggers them, so
nothing executes in the Airflow worker and there is no second dbt execution host
to configure.

The dlt and dbt legs are independently optional, so this item expresses a
dlt-only, a dbt-only, or a combined pipeline — the same shapes the Data Pipeline
target supports. materialize-airflow-job.py strips the leg that was not asked
for and emits the task chain for what remains; at least one leg is always
present, because a DAG with neither workload orchestrates nothing.

orchestration_support lives in the item's plugins/ folder — Fabric discards a
non-DAG .py placed at the top level of dags/.
"""
import json
from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.fabric.operators.run_item import MSFabricRunJobOperator

from orchestration_support import (committed_schedule, resolve_runner_coordinates, run_label,
                                   write_orchestration_run)

# One source for the connection name: it is passed to BOTH the operator and the
# resolver. Letting the resolver fall back to its own default made the DAG look
# for a connection the operator was not using.
FABRIC_CONN_ID = "@@FABRIC_CONN_ID@@"

# @@DLT_BEGIN@@
# The runner's two parameters, as literal Domain coordinates — the same values
# the Data Pipeline path writes into its TridentNotebook activity, never variable
# names. Fabric passes a notebook parameter through verbatim, so a committed
# "$VD_DOMAIN_SLUG" would reach the runner as those characters.
# Sent as the run-item POST body; the operator forwards job_params unchanged.
DLT_JOB_PARAMS = json.dumps({"executionData": {"parameters": {
    "DOMAIN_SLUG": {"value": "@@DOMAIN_SLUG@@", "type": "string"},
    "PIPELINE": {"value": "@@DLT_PIPELINE@@", "type": "string"},
}}})
DLT_RUNNER_NAME = "@@DLT_RUNNER@@"
# @@DLT_END@@
# @@DBT_BEGIN@@
# The row's dbt job notebook carries its own commands, so the DAG passes it what a Data
# Pipeline activity passes: DBT_OUTPUT_DIR, this DAG run's id made path-safe, naming the
# run's output folder (./dbt-job-notebook.md). job_params is a templated field, so it
# renders per run.
DBT_JOB_PARAMS = json.dumps({"executionData": {"parameters": {
    "DBT_OUTPUT_DIR": {"value": "{{ run_id | run_label }}", "type": "string"},
}}})
DBT_NOTEBOOK_NAME = "@@DBT_NOTEBOOK@@"
# @@DBT_END@@

# The cadence is NOT written here. It lives in plugins/dag_schedules.json, a
# Git-only part that customer CI/CD deploys and the ephemeral import never
# carries — so this same committed DAG runs to its real cadence in production and
# on-demand-only in the sandbox, and an ephemeral item cannot fire on its own
# after the intent ends (VD-5767). Never replace this call with a literal cron:
# the validator's committed-active-schedule rule rejects one, because the
# committed file would then disagree with the deployed DAG.
with DAG(
    dag_id="@@NAME@@",
    start_date=datetime(2026, 1, 1),
    schedule=committed_schedule("@@NAME@@"),
    catchup=False,
    max_active_runs=1,
    user_defined_filters={"run_label": run_label},
) as dag:

    # Workspace and item id are resolved in their own task, never at module
    # level: everything outside a task body runs on every scheduler parse loop,
    # so a REST lookup here would be re-issued every few seconds, and a missing
    # workspace id would surface as a DAG import error rather than a task
    # failure. `workspace_id` and `item_id` are template_fields on the operator,
    # so the pulls below render at execution time.
    #
    # job_type is case-sensitive on every run-item operator below. deferrable
    # defaults to True and is not restated; wait_for_termination exists only for
    # backwards compatibility and is deliberately not passed.
# @@DLT_BEGIN@@
    resolve_dlt = PythonOperator(
        task_id="resolve_dlt",
        python_callable=resolve_runner_coordinates,
        op_kwargs={"display_name": DLT_RUNNER_NAME, "item_type": "Notebook",
                   "conn_id": FABRIC_CONN_ID},
    )

    dlt_load = MSFabricRunJobOperator(
        task_id="dlt_load",
        fabric_conn_id=FABRIC_CONN_ID,
        workspace_id="{{ ti.xcom_pull(task_ids='resolve_dlt')['workspace_id'] }}",
        item_id="{{ ti.xcom_pull(task_ids='resolve_dlt')['item_id'] }}",
        job_type="RunNotebook",
        job_params=DLT_JOB_PARAMS,
        timeout=@@RUN_TIMEOUT@@,
    )
# @@DLT_END@@
# @@DBT_BEGIN@@
    resolve_dbt = PythonOperator(
        task_id="resolve_dbt",
        python_callable=resolve_runner_coordinates,
        op_kwargs={"display_name": DBT_NOTEBOOK_NAME, "item_type": "Notebook",
                   "conn_id": FABRIC_CONN_ID},
    )

    dbt_build = MSFabricRunJobOperator(
        task_id="dbt_build",
        fabric_conn_id=FABRIC_CONN_ID,
        workspace_id="{{ ti.xcom_pull(task_ids='resolve_dbt')['workspace_id'] }}",
        item_id="{{ ti.xcom_pull(task_ids='resolve_dbt')['item_id'] }}",
        job_type="RunNotebook",
        job_params=DBT_JOB_PARAMS,
        timeout=@@RUN_TIMEOUT@@,
    )
# @@DBT_END@@

    record_run = PythonOperator(
        task_id="record_run",
        python_callable=write_orchestration_run,
        op_kwargs={"conn_id": FABRIC_CONN_ID,
                   "code_lakehouse_name": "@@CODE_LAKEHOUSE_NAME@@",
                   "domain_slug": "@@DOMAIN_SLUG@@"},
        trigger_rule="all_done",
    )

    # The DAG run's own state is computed from its LEAF tasks. record_run is
    # all_done and swallows its failures, so with it as the only leaf a run whose
    # dlt or dbt task failed still reported `success` — run-verified, VD-5578.
    # This leaf inherits the workload's fate (default all_success trigger rule),
    # so the DAG run fails when the workload does. Never give it all_done, and
    # never make record_run the last task again.
    workload_succeeded = EmptyOperator(task_id="workload_succeeded")

    @@CHAIN@@
