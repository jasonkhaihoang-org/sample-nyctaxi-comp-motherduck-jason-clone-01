# Orchestration evaluation — Fabric

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

The Fabric validators and evidence for evaluating orchestration in `generating-orchestration`, shared by both Fabric platforms.

## Validators

`python3 "$SKILL_DIR/../../scripts/platforms/_family/fabric/validate-datapipeline.py" orchestration/<Name>.DataPipeline --repo-root .` for a pipeline — JSON shape, activity names, dependency resolution and cycles, the runner contract of every `TridentNotebook` activity (literal parameters, a flat `notebookId`, a dbt job notebook's `DBT_OUTPUT_DIR`), unresolved placeholders, embedded secrets, native `.schedules` schema, `.platform` sanity. The validators own these rules; never re-implement, second-guess, or hand-roll them locally — extend the script, with tests, when a rule is missing. Tests exercise the committed definition only, never one regenerated from a design record.

On the **Airflow** target the item is `orchestration/<Name>.ApacheAirflowJob/` and the validator is `python3 "$SKILL_DIR/../../scripts/platforms/_family/fabric/validate-airflow-dag.py" orchestration/<Name>.ApacheAirflowJob --repo-root .` — item shape, `.platform` identity, pinned requirements and versions, committed secrets and literal GUIDs in DAG source, a present and non-gating `record_run`, a DAG Fabric would drop or fail to parse, worker-side dbt, `dual-orchestration-target` when the repo commits a Data Pipeline item alongside, and `missing-dbt-job-notebook` when a dbt leg names no committed dbt job notebook. A domain on this target commits the **same** notebooks the native target would — the DAG triggers them.

## Invoked artifacts

On the Airflow target the same check reads the DAG instead of the activity list: its `DLT_RUNNER_NAME` must match a committed `orchestration/<name>.Notebook/` and its `DBT_NOTEBOOK_NAME` a committed dbt job `orchestration/<name>.Notebook/`, whose run cell's selector must then resolve in the committed `transformation/` project.

## Evidence

An ephemeral pipeline-run terminal status for a `create`, `recreate`, or a `modify` touching `pipeline-content.json`, an invoked runner, or the dbt project — and, when the pipeline has a dbt activity, the `get-dbt-job-evidence.py` line (pipeline run id, start time, `defer=on|off`, all-green `run_results.json`); running a notebook on its own never satisfies this. Also the `.platform` identity-check outcome for any `modify`, and the directory's absence plus the removal commit for a `delete`. A schedule-only `modify` and a `delete` carry no run evidence by construction — that absence is correct, not a missing gate.
