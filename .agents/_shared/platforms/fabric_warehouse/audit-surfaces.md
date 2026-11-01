# Fabric Warehouse — audit surfaces

Where Fix reads runtime evidence on this engine.
A Warehouse is the T-SQL engine itself: no SQL-endpoint sync lag on its own tables and no Spark-side surfaces.

| Read need | Surface | Latency | Notes |
| --- | --- | --- | --- |
| Run audit | Monitor hub / job-instance API; native Fabric job and activity-run history | near-live | audit-read only, never a read-gate surface |
| Deep logs | dbt job evidence on the Ephemeral Paired Lakehouse, `Files/<slug>/runs/<pipeline run id>/` | every run | no size cap; record the OneLake path as the pointer |
| DQ + run/test results | Elementary (`elementary_test_results`, `dbt_run_results`); dbt artifacts; dlt `audit_runs` | per run | Elementary is present on this engine (below) |
| Lineage | dbt manifest (source of truth); OneLake catalog secondarily | at rest | native lineage enriches, never gates |
| `git_sha` pivot | `_git_sha` / `_dbt_invocation_id` mart columns | per run | the only stamped surface; `../../references/conventions/runtime-audit-columns.md` |

**Elementary is present on this engine.** The seeded `transformation/packages.yml` takes `elementary-data/elementary` (`>=0.15.0 <1.0.0`) from the hub and its hooks run under `dbt-fabric`.
The Lakehouse's `elementary_fabricspark` vendoring and overrides do not apply here.
That the hooks run does not prove every table is populated: read them, name any missing one, and fall back to dbt artifacts, dlt `audit_runs` and the mart stamps.

## Plane 2 — runtime-audit retrieval

The deployed product is in the **domain workspace**: resolve `<domain_workspace>` from `VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_NAME`.
Use `VD_EPHM_FABRIC_WAREHOUSE_WORKSPACE_NAME` only when the run under investigation happened in the sandbox.

<!-- not-a-runnable-fence: the second call takes a run id from the first -->
```bash
fab job run-list "<domain_workspace>.Workspace/<pipeline>.DataPipeline"            # discover recent run ids
fab job run-status "<domain_workspace>.Workspace/<pipeline>.DataPipeline" --id <run-id>
```

- Deep logs: navigate the Ephemeral Paired Lakehouse's `Files/<slug>/runs/<pipeline run id>/` with `fab ls`/`fab get` ([`fab-cli-cheatsheet.md`](../_family/fabric/fab-cli-cheatsheet.md)).
- Run/test results: read dbt artifacts directly, e.g. `jq '.results[] | select(.status!="success" and .status!="pass")' target/run_results.json`, and dlt `audit_runs` over TDS for ingestion runs.
- Degradation: native job surface absent or preview-gated → those artifacts; record it.

### git_sha pivot

```sql
SELECT DISTINCT _git_sha, _dbt_invocation_id, _loaded_at
FROM <anchor> WHERE <predicate> ORDER BY _loaded_at DESC;   -- via lakehouse_query
```

Then `git show <_git_sha>`, and correlate the invocation to `target/run_results.json` `.metadata.invocation_id`.
Unstamped provenance: `git log` over the implicated files plus artifact timings, at reduced confidence; there is no Elementary run-side `git_sha` to fall back to.

Plane-3 navigation and probes: [`context-plane-probes.md`](../../references/guides/context-plane-probes.md).

## Plane 3 — read-only Warehouse access

**Primary: the native `lakehouse_query` and `lakehouse_schema` tools**, which open a Warehouse target directly despite the name.

- Pass `target: "domain"` for the deployed product, `target: "ephemeral"` only for a run in the sandbox. Studio resolves the endpoint and mints the session-identity token; never touch credential variables (`./dialect.md` § Identity Boundary).
- Read-only comes from the identity's grants, not the tool: `lakehouse_query` passes statements through unfiltered, so send only reads.
- Read identifiers with `lakehouse_schema` (`schemaType: "columns"`, optional `tableFilter`), then probe with `lakehouse_query`.
- Output is capped at 256 KB; a larger result returns leading rows with `Results truncated`. Use aggregates or `SELECT TOP n`, and narrow and re-run when truncated.
- T-SQL: `SELECT TOP n`, `SYSUTCDATETIME()`, three-part `<warehouse>.<schema>.<table>`.

Two Lakehouse caveats do **not** apply:

- There is **no SQL-endpoint sync lag** on the Warehouse itself: an `Invalid object name` there means the relation is not there (wrong schema, wrong target, failed build). List the ephemeral schema with `lakehouse_schema` first: a relation this Intent built must be there, so its absence is a real defect. A production table this Intent did not build is read through the Ephemeral Paired Lakehouse and may not have synced yet; reopening the Intent re-mirrors it, so never report it absent from that read alone.
- There is **no materialized-lake-view surface**: the tools gate it to Lakehouse; do not look for it or report its absence.

**Fallback: `fab get` + T-SQL**, only outside Studio's runtime; it never applies inside an Intent, where a probe the native tools cannot express is a recorded RCA gap.

```bash
fab get "<domain_workspace>.Workspace/<warehouse>.Warehouse"   # connection string / SQL endpoint
```

The endpoint is also `VD_DOMAIN_FABRIC_WAREHOUSE_SQL_ENDPOINT` (`VD_EPHM_FABRIC_WAREHOUSE_SQL_ENDPOINT` for the sandbox).
On this path read-only is procedural: a workspace role is the whole grant, so Contributor or above can write; record that as a degradation.
Roles are workspace-grain: state the grain when a conclusion depends on identity scoping.

## Orchestration Pipeline run-ID ingress

A dbt run through a job's dbt notebook leaves `Files/<slug>/runs/<pipeline run id>/` in the Ephemeral Paired Lakehouse: dbt's `target/` (`run_results.json` with the `invocation_id`, `manifest.json`, compiled SQL) and `dbt.log`, one folder per run named by `DBT_OUTPUT_DIR` (an Airflow run uses its `dag_run_id` made path-safe).
Nothing prunes the folders: correlate a past run to its dbt invocation through its folder and the Elementary tables it wrote, never by timestamp.
The notebook builds with the committed `transformation/profiles.yml` (`prod`) or, in an Intent, the Intent's `fab_notebook_profile/profiles.yml` (`ephemeral_platform`).
A dlt run has no correlation field; native Fabric job and activity-run history is its audit trail.
