# Redshift — audit surfaces

The baseline tables, pointers, degradations and `git_sha` pivot are those in [`../_family/duckdb/audit-surfaces.md`](../_family/duckdb/audit-surfaces.md), with these differences:

- The tables live where the investigated run wrote: the Domain database for a deployed run, the sandbox for a Build or Fix run; say which answered.
- Query history is in `SYS_QUERY_HISTORY`.

## Plane 2 — runtime-audit retrieval

- No plugin-side SQL client: run reads through dbt from `transformation/` as `dbt show --inline '<sql>' --limit 20`.
- Never assemble a connection string.
- Name Domain relations by three parts; `<domain_db>` is `VD_DOMAIN_REDSHIFT_DATABASE`.

```sql
select load_id, pipeline_name, status, started_at, finished_at
from <domain_db>.<source_schema>.audit_runs order by started_at desc limit 20;

select r.started_at, l.table_name, l.rows_extracted, l.rows_normalized, l.load_state
from <domain_db>.<source_schema>.audit_table_loads l join <domain_db>.<source_schema>.audit_runs r using (load_id)
where l.table_name = '<table>' order by r.started_at desc limit 20;

select invocation_id, name, status, execution_time, generated_at
from <domain_db>.<elementary_schema>.dbt_run_results where generated_at >= '<window_start>' order by generated_at desc;

select invocation_id, test_unique_id, status, failures, detected_at
from <domain_db>.<elementary_schema>.elementary_test_results where detected_at >= '<window_start>' and status != 'pass';
```

## Plane 3 — read-only warehouse access

- Cross-database queries are read-only by engine, so Domain reads are engine-enforced read-only.
- The sandbox is writable by the same credential, so scope probes to `<domain_db>` unless the run happened in the sandbox.
- Then run [`../../references/guides/context-plane-probes.md`](../../references/guides/context-plane-probes.md), preferring aggregates; the first probe may wait about a minute for a Serverless resume.
