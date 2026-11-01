# Orchestration stages — Fabric

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

The Fabric half of each stage of the `orchestration` kind playbook, shared by both Fabric platforms.

## Intent

- **Orchestration target**: the native `.DataPipeline` with the notebooks it invokes (default, recommended) or a `.ApacheAirflowJob` (`./airflow-job.md`).
- The committed `orchestration/` declares the target; a committed item of either kind is a fact for every later intent. There is no configuration file. A dlt runner or dbt job `.Notebook` never decides it.
- Only when `orchestration/` holds neither is the target an Intent decision. Recommend Data Pipeline; offer Airflow when the user names it as their standard, saying it is opt-in and that a dlt leg needs an `azure_key_vault` Domain. One target per domain, never per intent.
- Before recommending Airflow, check the shape against "Target and shape" in `./airflow-job.md`; Generate cannot author a shape marked **no**.

## Design

Recommend Orchestration Pipelines as the playbook's Design section says; a row's `Target` is `datapipeline` or `airflow`, the target `## Intent` resolved.
A `modify` row's `Reason` says whether `pipeline-content.json` is touched or only `.schedules` (Data Pipeline), or whether anything beyond `plugins/dag_schedules.json` is touched (Airflow); that decides whether the plan needs an ephemeral run.

## Plan

A `create` over a committed item would replace its `logicalId` and orphan the deployed object; the playbook's presence rule halts on it.

### Data Pipeline target

| Action | Steps | Deterministic gate |
| --- | --- | --- |
| `create` | Generate → Ephemeral run | validator exit 0, then the job reaching `Completed` |
| `modify` touching `pipeline-content.json`, an invoked notebook, or `transformation/` | Generate → Ephemeral run | as `create`, plus the identity check |
| `modify` touching only `.schedules` | Generate | validator exit 0 plus the identity check; no ephemeral run, because the import carries no schedule |
| `delete` | Remove | the item directory is gone and the removal commit is cited from `git log` |
| `recreate` | Remove → Generate → Ephemeral run | as `create`; identity deliberately not preserved |

### Airflow target

Never plan a shape `./airflow-job.md` marks **no**.

| Action | Steps | Deterministic gate |
| --- | --- | --- |
| `create` | Generate → Ephemeral run | `validate-airflow-dag.py` exit 0, then the DAG run reaching success with every task instance green |
| `modify` | Generate → Ephemeral run | as `create`, plus the identity check |
| `modify` touching only `plugins/dag_schedules.json` | Generate | `validate-airflow-dag.py` exit 0 plus the identity check; no ephemeral run. Edit the file directly; `materialize-airflow-job.py` refuses an existing item and `recreate` would replace the `logicalId` |
| `delete` | Remove | the item directory is gone and the removal commit is cited from `git log` |
| `recreate` | Remove → Generate → Ephemeral run | as `create`; identity deliberately not preserved |

- A literal schedule in the DAG is a `committed-active-schedule` finding: it would keep firing in the ephemeral workspace after the intent ends.
- A `modify` changing `airflowRequirements`, or adding a file, needs the job **restarted** before its run proves anything; an edit to a deployed DAG does not (`./airflow-job.md`).

### Steps

**Identity check (every `modify`).** Before committing, `git diff HEAD -- orchestration/<Name>.<Kind>/.platform` (the item and every item it invokes) must show no `logicalId` change; a change halts the task. Record the command and outcome in `## Execution evidence`. Only `recreate` may change identity.

**Generate**: a step invoking `generating-orchestration` (`./orchestration-authoring.md`), authoring `orchestration/<Name>.DataPipeline/` (`pipeline-content.json`, plus `.schedules` when Schedule is not `none`) and the items it invokes: each dbt job's `orchestration/<job>_dbt.Notebook/`, and on Airflow any dlt runner `.Notebook`. A dbt-only row still gets a one-activity pipeline. Gate: `python3 "$SKILL_DIR/../../scripts/platforms/_family/fabric/validate-datapipeline.py" orchestration/<Name>.DataPipeline --repo-root .` exits 0, or `validate-airflow-dag.py` on Airflow, recorded in `## Execution evidence`.

**Ephemeral run**: a step invoking `generating-orchestration`'s sandbox run (`./orchestration-running.md`). Gate: the pipeline run reaching `Completed` plus the all-green `get-dbt-job-evidence.py` line per dbt activity, or the Airflow DAG run gate.

## Verify

- **Native artifact validation**: every `.DataPipeline` and the items it invokes via `validate-datapipeline.py --repo-root .`, or every `.ApacheAirflowJob` via `validate-airflow-dag.py --repo-root .` (`./orchestration-evaluating.md`).
- **Ephemeral run evidence**: a `Completed` pipeline run (or a successful DAG run) plus the all-green dbt evidence line for each dbt activity or dbt leg. A schedule-only `modify` and a `delete` carry no run evidence by construction; that is not a gap.
- **Lifecycle evidence**: a `modify` row's gate outcome is its identity-check outcome.

## Ship

Customer-owned CI/CD deploys the committed item directories with Fabric Git integration, `fabric-cicd`, the Fabric CLI, or the REST APIs.
