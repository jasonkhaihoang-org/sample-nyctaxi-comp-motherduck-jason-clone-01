# Fabric Lakehouse — audit surfaces

Where Fix reads runtime evidence on this engine.
Native surfaces are often absent or preview-gated; the baseline (Elementary + dbt artifacts + dlt audit) is the floor, and every fallback is recorded as a degradation.

| Read need | Surface | Latency | Notes |
| --- | --- | --- | --- |
| Run audit | Monitor hub / job-instance API; Eventhouse KQL job logs where present | near-live | audit-read only, never a read-gate surface |
| Deep logs | dbt job evidence on OneLake, `Files/<slug>/runs/<pipeline run id>/` | every run | no size cap; record the OneLake path as the pointer |
| DQ results | Elementary result tables; Purview DQ additively where present | per run | |
| Lineage | dbt manifest (source of truth); OneLake catalog secondarily | at rest | native lineage enriches, never gates |
| `git_sha` pivot | `_git_sha` / `_dbt_invocation_id` model columns | per run | `../../references/conventions/runtime-audit-columns.md`; Elementary's run-side `git_sha` is off by default (below) |

## Plane 2 — runtime-audit retrieval

The deployed product is in the **domain workspace**: resolve `<domain_workspace>` from `VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_NAME`.
Use `VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME` only when the run under investigation happened in the sandbox.

<!-- not-a-runnable-fence: the second call takes a run id from the first -->
```bash
fab job run-list "<domain_workspace>.Workspace/<pipeline>.DataPipeline"            # discover recent run ids
fab job run-status "<domain_workspace>.Workspace/<pipeline>.DataPipeline" --id <run-id>
```

- Eventhouse KQL job logs: pointer is the job run id; state the near-live latency.
- Deep logs: navigate `Files/<slug>/runs/<pipeline run id>/` with `fab ls`/`fab get` ([`fab-cli-cheatsheet.md`](../_family/fabric/fab-cli-cheatsheet.md)).
- DQ and run/test results: query Elementary through `lakehouse_query` with T-SQL three-part names, `<lakehouse>.<elementary_schema>.elementary_test_results` and `<lakehouse>.<elementary_schema>.dbt_run_results` (`TOP n`, not `LIMIT n`; resolve `<elementary_schema>` from the manifest). Read `target/run_results.json` / `target/manifest.json` directly, e.g. `jq '.results[] | select(.status!="success" and .status!="pass")' target/run_results.json`.
- **Autoload caveat:** the Fabric `dbt_project.yml` sets `disable_run_results`, `disable_dbt_invocation_autoupload` and `disable_dbt_artifacts_autoupload` to `true`, so `dbt_run_results` and Elementary's run-side `git_sha` are empty unless the domain re-enabled them; check the deployed `dbt_project.yml` and record the gap. `elementary_test_results` still populates.
- Pointer: `<elementary_schema>.elementary_test_results` + `test_unique_id`, or the artifact path.
- Degradation: native job surface absent → Elementary + dbt artifacts; Elementary absent or run-results disabled → dbt artifacts + OneLake job logs. Say so.

### git_sha pivot

The mart-side stamps are the primary surface here:

```sql
SELECT DISTINCT _git_sha, _dbt_invocation_id, _loaded_at
FROM <anchor> WHERE <predicate> ORDER BY _loaded_at DESC;   -- via lakehouse_query / the SQL analytics endpoint
```

Then `git show <_git_sha>`, and correlate the invocation to `target/run_results.json` `.metadata.invocation_id`, or to `<elementary_schema>.dbt_run_results` where re-enabled.
Unstamped provenance: `git log` over the implicated files plus artifact timings, at reduced confidence.

Plane-3 navigation and probes: [`../../references/guides/context-plane-probes.md`](../../references/guides/context-plane-probes.md).

## Plane 3 — read-only lakehouse access

**Primary: the native `lakehouse_query` and `lakehouse_schema` tools** on the Lakehouse SQL analytics endpoint.

- Pass `target: "domain"` for the deployed product, `target: "ephemeral"` only for a run in the sandbox. Studio resolves the endpoint and mints the session-identity token; never touch credential variables (`./dialect.md` § Identity Boundary).
- Read-only comes from the identity's grants, not the tool: `lakehouse_query` passes statements through unfiltered, so send only reads.
- Read identifiers with `lakehouse_schema` (`schemaType: "columns"`, optional `tableFilter`), then probe with `lakehouse_query`.
- Output is capped at 256 KB; a larger result returns leading rows with `Results truncated`. Use aggregates or `SELECT TOP n`, and narrow and re-run when truncated.
- T-SQL dialect at the endpoint: `SELECT TOP n`, `SYSUTCDATETIME()`, three-part `<lakehouse>.<schema>.<table>`.

**SQL-endpoint sync lag.** The endpoint syncs Spark-written Delta tables lazily, so a just-built table can be `Invalid object name` there while `dbt test` sees it.
Treat that as lag, not a broken mart: call `refresh_sql_metadata` first (`./dialect.md` § "Querying the SQL endpoint"); if the table is still absent, read freshness from current surfaces (source/bronze maxima, `audit_runs` success and `finished_at`, `_loaded_at`), record the lag as a degradation, or read the Delta from OneLake as a last resort.
A relation still absent after the lag window that is configured as a **view** is not lag: the endpoint exposes Delta tables only, so a dbt model built as a Spark view never appears there (`./dialect.md` § "Read-back models are tables").
Decide which it is from the model's configured materialization in the dbt project (its `config()`, `models:` in `dbt_project.yml`, or `config.materialized` in `target/manifest.json`), not from the endpoint, which answers `Invalid object name` for both.

**Fallback: `fab get` + T-SQL**, only outside Studio's runtime; it never applies inside an Intent, where a probe the native tools cannot express is a recorded RCA gap.
A native call refused inside an Intent is the same gap: never reach the Lakehouse item, its `Tables/` or its SQL endpoint through `fab` instead, which there reads only Plane 2's job runs and `Files/` deep logs.

```bash
fab get "<domain_workspace>.Workspace/<lakehouse>.Lakehouse"   # sqlEndpointProperties.connectionString
```

On this path read-only is engine-enforced only when the identity is **Viewer** on the domain workspace; Contributor or above makes it procedural, which is a degradation to record.
Roles are workspace-grain: state the grain when a conclusion depends on identity scoping.

## Orchestration Pipeline run-ID ingress

A dbt run through a job's dbt notebook leaves `Files/<slug>/runs/<pipeline run id>/` in the code Lakehouse: dbt's `target/` (`run_results.json` with the `invocation_id`, `manifest.json`, compiled SQL) and `dbt.log`, one folder per run named by `DBT_OUTPUT_DIR` (an Airflow run uses its `dag_run_id` made path-safe).
Nothing prunes the folders: correlate a past run to its dbt invocation through its folder and the Elementary tables it wrote, never by timestamp.
A dlt run has no correlation field; native Fabric job and activity-run history is its audit trail.
