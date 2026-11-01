# DuckDB / MotherDuck — audit surfaces

Where Fix reads runtime evidence on the DuckDB engine, local file or MotherDuck.
There is no native job store or lineage; the generated baseline below is the only surface.

| Read need | Surface | Pointer to record |
| --- | --- | --- |
| Run audit | dlt `<source_schema>.audit_runs` | `load_id` |
| Per-table load volume | dlt `<source_schema>.audit_table_loads` | `load_id` + `table_name` |
| dbt run and test results | Elementary `<elementary_schema>.dbt_run_results`, `elementary_test_results` | `invocation_id` / `test_unique_id` |
| dbt artifacts | `target/run_results.json`, `target/manifest.json` | file path + `.metadata.invocation_id` |
| Lineage | dbt manifest + dlt schema | file path |
| `git_sha` pivot | `audit_runs.git_sha` when the column exists and the value is not null; mart columns `_git_sha`, `_dbt_invocation_id` (`../../../references/conventions/runtime-audit-columns.md`) | the `_git_sha` + `_dbt_invocation_id` pair |
| Deep logs | `logs/dbt.log` and dlt log files in the workspace | file path |

`<elementary_schema>` is the dbt target schema Elementary materializes into, not a schema named `elementary`.
Resolve it with `jq -r '.nodes["model.elementary.dbt_run_results"].relation_name' target/manifest.json`.

## Plane 2 — runtime-audit retrieval

```sql
SELECT load_id, pipeline_name, status, started_at, finished_at
FROM <source_schema>.audit_runs ORDER BY started_at DESC LIMIT 20;

SELECT r.started_at, l.table_name, l.rows_extracted, l.rows_normalized, l.load_state
FROM <source_schema>.audit_table_loads l JOIN <source_schema>.audit_runs r USING (load_id)
WHERE l.table_name = '<table>' ORDER BY r.started_at DESC LIMIT 20;

SELECT invocation_id, name, status, execution_time, generated_at
FROM <elementary_schema>.dbt_run_results WHERE generated_at >= '<window_start>' ORDER BY generated_at DESC;

SELECT invocation_id, test_unique_id, status, failures, detected_at
FROM <elementary_schema>.elementary_test_results WHERE detected_at >= '<window_start>' AND status != 'pass';
```

<!-- not-a-runnable-fence: two independent artifact reads -->
```bash
jq '.metadata.invocation_id' target/run_results.json
jq -r '.results[] | select(.status!="success" and .status!="pass") | "\(.unique_id)\t\(.status)"' target/run_results.json
```

A missing surface is a recorded gap with lowered confidence, never a silent fallback:

| Missing | Fall back to |
| --- | --- |
| `audit_runs` or Elementary tables (fresh or dlt-only project, or no Elementary package) | `target/run_results.json`; anomaly-tier checks are unavailable |
| `target/` absent or stale for the window | `audit_runs` and Elementary alone |
| Log file rotated or missing | the structured surfaces above |
| `audit_runs.git_sha` null, or absent from `lakehouse_schema` (`schemaType: "columns"`) on `audit_runs` — check before selecting it | the mart's `_git_sha`, else `git log --since=<window_start> -- ingestion/` intersected with run timings |
| `_git_sha` / `_dbt_invocation_id` blank on the mart | `git log --since=<window_start> -- <model files>` intersected with run timings |

### git_sha pivot

```sql
SELECT DISTINCT _git_sha, _dbt_invocation_id, _loaded_at
FROM <anchor> WHERE <predicate isolating the wrong rows> ORDER BY _loaded_at DESC;
```

<!-- not-a-runnable-fence: pivot reads, run one at a time -->
```bash
git show <_git_sha> --stat
git log <_git_sha> -1 --format='%H %ci %s'
```

Match `_dbt_invocation_id` to `run_results.json` `.metadata.invocation_id` or `dbt_run_results.invocation_id`.

## Plane 3 — read-only lakehouse access

- Use the native `lakehouse_schema` (`schemaType: "columns"`) and `lakehouse_query` tools with `target: "domain"`, or `target: "ephemeral"` only when the investigated run happened in the sandbox.
- Never pass a platform kind, coordinates or credential, and never read, print or set a token.
- `lakehouse_query` does not filter statements: run only reads, and prefer aggregates (`MAX`, `COUNT`) over scans.
- Output is capped at 256 KB; a `Results truncated` notice means narrow the query and re-run.
- Then run the probes in [`../../../references/guides/context-plane-probes.md`](../../../references/guides/context-plane-probes.md) against the anchor.
- Inside an Intent the native tools are the only route, because `motherduck_token` there is a placeholder.
  A probe they cannot express is a recorded RCA gap, never a reason to `ATTACH`, `duckdb -readonly` or `duckdb.connect`.

Outside Studio only, a client-side open is a recorded degradation:

| Engine | Open | Read-only strength |
| --- | --- | --- |
| Local file | `ATTACH '/data/duckdb/<slug>.duckdb' AS dom (READ_ONLY);`, `duckdb -readonly <file>`, or `duckdb.connect(<file>, read_only=True)` | client-side only |
| MotherDuck | `ATTACH 'md:<db>' (READ_ONLY);` | engine-enforced only under a read-scoped token; the runtime normally carries a read-write one, so procedural |
