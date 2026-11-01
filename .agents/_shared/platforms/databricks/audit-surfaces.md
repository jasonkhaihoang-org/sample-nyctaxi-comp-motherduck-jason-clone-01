# Databricks — audit surfaces

Where Fix reads runtime evidence on this engine.

| Read need | Surface | Latency | Notes |
| --- | --- | --- | --- |
| Load audit | `audit_runs` and `audit_table_loads` in the loaded dataset | per load | the pipeline notebook writes them through `persist_audit`, on failure too |
| Run audit | Lakeflow Jobs run history | per run | the deployed job's runs; the pointer is the run id or run URL |
| Task output | a task run's output | per run | notebook exit value and error; capped at 5 MB, kept 60 days |
| DQ results | Elementary result tables, where installed | per run | |
| Lineage | dbt manifest | at rest | |
| `git_sha` pivot | `_git_sha` / `_dbt_invocation_id` model columns | per run | `../../references/conventions/runtime-audit-columns.md` |

## Plane 2 — runtime-audit retrieval

The deployed product reads from the production catalog `VD_DOMAIN_DATABRICKS_CATALOG`; use the Ephemeral catalog `VD_EPHM_DATABRICKS_CATALOG` only when the run under investigation happened in the sandbox. Read the audit tables with `lakehouse_query` by three-part name, `<catalog>.<dataset>.audit_runs`, where `<dataset>` is the pipeline's `dataset_name`: on the `domain` target for a deployed run, which loads into that schema unprefixed, and on `ephemeral` for a sandbox run, whose dataset carries the Intent's prefix (`<VD_EPHM_SCHEMA_PREFIX><dataset>`).

<!-- not-a-runnable-fence: each later call takes an id from the one before -->
```bash
databricks jobs list-runs --job-id <job-id> --limit 20 -o json   # recent runs of the deployed job
databricks jobs get-run <run-id> -o json                         # its tasks and their own run ids
databricks jobs get-run-output <task-run-id> -o json             # one task's output, by the task's run id
```

- `get-run-output` takes a task's run id (`tasks[].run_id` from `get-run`), not the job run's.
- Degradation: no run history reachable → the audit tables and dbt artifacts. Say so.
