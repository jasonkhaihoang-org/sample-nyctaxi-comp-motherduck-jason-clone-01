# Orchestration — Databricks

The native item is a Lakeflow job in the Domain's Declarative Automation Bundle: `orchestration/<job>.job.yml`, included by `databricks.yml` at the repository root. A dlt task runs the committed pipeline notebook `ingestion/<name>_pipeline.ipynb`; a dbt task runs the dbt project on the Domain's SQL warehouse.
`SKILL_DIR` below is `SKILL_DIR=<this skill's directory>`, the skill that sent you here; substitute it, the runtime does not expand it.

The gate, used by Plan, Authoring, Evaluate and Document:

```bash
SKILL_DIR="<this skill's directory>" && cd /workspace && python3 "$SKILL_DIR/../../scripts/platforms/databricks/validate-job.py" --repo-root .
```

It checks the bundle and every job file: no committed coordinates, the `sandbox` and `prod` targets with no default, no `run_as` or permissions, a schedule paused through `${var.schedule_pause_status}`, serverless environment version 5, installs under the managed constraints, notebook parameters equal to the notebook's widgets with `dlt_env` passed as `${var.dlt_env}`, the dbt task waiting on every dlt task and taking `VD_EPHM_SCHEMA_PREFIX` from `${var.schema_prefix}`, and a dbt project whose `profile:` is a plain name.

## Intent

One native item, so no target choice and no platform branch.

## Design

Zero, one or several jobs, one per independently operated workload boundary, each running its dlt notebooks in parallel and then its dbt selection. Read `Lakeflow job` for `Orchestration Pipeline`; a row's `Target` is `job`.

## Plan

| Action | Steps | Gate |
| --- | --- | --- |
| `create` | Generate → Sandbox run | validator exit 0, then a green run |
| `modify` touching tasks, parameters, environments or the invoked notebook or dbt selection | Generate → Sandbox run | as `create` |
| `modify` touching only `schedule` | Generate | validator exit 0; no run, the sandbox never activates a schedule |
| `delete` | Remove | job file gone and removal commit cited from `git log` |
| `recreate` | Remove → Generate → Sandbox run | as `create` |

- Generate and Sandbox run are `generating-orchestration` steps; record each gate in the Plan's `## Execution evidence`.
- No identity check on `modify`: a job's identity is its key in the job file, which a `modify` keeps.

## Verify

The validator, plus the green run's log; a `modify` row is covered by its gate outcome.

## Ship

- Customer CI/CD deploys with `databricks bundle deploy -t prod`, passing the Domain's `warehouse_id`, `catalog` and `schema` and `schedule_pause_status=UNPAUSED`; the job runs as the principal that deploys it, which the Domain owner grants.
- Studio never deploys `prod` and never activates a schedule.
- The dbt task's environment variable needs the workspace preview **Environment variables in Lakeflow Jobs**, which a workspace admin enables; enabling it is the user's to do.

## Authoring

- `databricks.yml`: copy `./templates/databricks.yml` to the repository root when absent and set `bundle.name` to the Domain slug; an existing one missing a variable the template declares gains it with the template's default, and one whose `dlt_env` defaults to `"{}"` takes the template's default, without which a production run has no catalog. Never add a host, a variable value, `run_as` or permissions.
- Each job: copy `./templates/orchestration.job.yml` to `orchestration/<job>.job.yml`, then set its key and name, `max_concurrent_runs` (1 unless the design says otherwise), the Quartz cron and timezone the design gives, one notebook task per dlt pipeline (parameters as the template has them, `pipeline_name` and `connection_name` from that notebook's widgets), and the dbt task's `--select`. An existing notebook task missing a parameter the template has gains it; an existing job missing the template's `environment_variables` entry, or a dbt task missing its `environment_variables_key`, gains them, with the template's environment version. A job with no dlt pipeline drops the notebook task, its environment and the `depends_on`; one with no dbt work drops the dbt task and its environment.
- A `delete` removes the job file only; `databricks.yml` stays while another job remains.
- Run the gate until exit 0.

## Sandbox run

The job runs on Databricks, deployed from the committed bundle to the `sandbox` target and destroyed after the run. Commit first: the deploy uploads the repository as it is on disk.

Run the job once, giving each run its own `<log>` file. It lasts as long as its loads and dbt build together: launch it with `start_async_bash` and `timeout_seconds: 3600`, with `$SKILL_DIR`, `<job_key>` and `<log>` substituted, and wait with `wait_for_async_bash`.

```bash
cd /workspace && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" 'python3 "$SKILL_DIR/../../scripts/platforms/databricks/run_job.py" --job <job_key> --log <log>'
```

- Green = exit 0: the run succeeded, every task included. The log carries the run URL and each task's outcome.
- Exit 1 (`RUN_FAILED`) is the run's own failure; exit 2 (`RUN_NOT_STARTED`) is the environment or the deploy. A permission, scope or credential error is the user's to fix: report the exact message and stop.
- The dlt tasks run with no row cap, so the run loads the full source; the dbt task builds under the Intent's prefix and reads its sources from this run's loads.
- Output or a log naming `sandbox deployment not destroyed` needs `databricks bundle destroy -t sandbox` with the same variables; report it.
- Static validation is not run evidence.

## Evaluate

The gate per committed bundle; a job file it reports, or a schedule that is not paused through the variable, is a **critical finding**.

## Document

- Read `orchestration/<job>.job.yml`: the tasks in dependency order, and the schedule as its Quartz cron in its own `timezone_id`.
- The schedule is committed paused and runs once customer CI/CD deploys `prod`; never describe it as running.
- Convert it to the Plan's local time (show the arithmetic) before comparing; halt for a conflict only if the converted time still disagrees.
- Validate each documented job with the gate above.
