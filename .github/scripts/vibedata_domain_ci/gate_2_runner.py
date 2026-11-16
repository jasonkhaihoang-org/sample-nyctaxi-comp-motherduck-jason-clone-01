"""Thin shell for the MotherDuck Gate 2 (ci/run) setup steps.

Subcommands:
    clone --pr N --head-sha SHA --domain SLUG --prod-db NAME
        Creates the per-PR database from prod; sets outputs db_name and
        head_sha_short. Reads MOTHERDUCK_TOKEN.
    drop-stale --pr N --db-name NAME --domain SLUG
        Best-effort drop of this PR's older per-SHA databases. Reads MOTHERDUCK_TOKEN.
    select --head-sha SHA
        Writes reports/gate2_select.txt from the deployment manifest (empty when
        the manifest has no artifacts).
    assemble --head-sha SHA --db-created true|false --db-name NAME
        Assembles reports/gate-2.json from $PROJ/target/run_results.json, sets
        output `passed`, and exits 1 when the build failed so the job's own
        conclusion reflects the dbt result.
"""

import argparse
import json
import os
import sys

from vibedata_domain_ci import ci_database
from vibedata_domain_ci import gate_2_result
from vibedata_domain_ci import runner_io
from vibedata_domain_ci.parse_run_results import results_from_command
from vibedata_domain_ci.write_modified_json import modified_names


def _connect():
    import duckdb  # lazy: only MotherDuck jobs install it, and the package declares no duckdb dependency

    return duckdb.connect(f"md:?motherduck_token={os.environ['MOTHERDUCK_TOKEN']}")


def _clone(args) -> None:
    head_sha_short = args.head_sha[:7]
    db_name = ci_database.derive_ci_database_name(args.domain, int(args.pr), head_sha_short)
    sql = ci_database.create_database_from_prod_sql(db_name, args.prod_db)

    con = _connect()
    try:
        con.execute(sql)
    except Exception as e:
        if "retention" in str(e).lower():
            # Free-plan: prd has >0 snapshot retention which the plan can't inherit.
            # Reset prd to 0-day retention and retry. No-op on paid plans (CREATE
            # succeeds on the first try and this block is never reached).
            con.execute(ci_database.clear_db_retention_sql(args.prod_db))
            con.execute(sql)
        else:
            raise
    con.close()

    runner_io.set_output("db_name", db_name)
    runner_io.set_output("head_sha_short", head_sha_short)
    print(f"Created MotherDuck database: {db_name}")


def _drop_stale(args) -> None:
    con = _connect()
    rows = con.execute("SHOW DATABASES;").fetchall()
    stale = ci_database.stale_pr_databases(
        [r[0] for r in rows], domain_slug=args.domain, pr_number=int(args.pr), current_db_name=args.db_name
    )
    print(f"Stale databases to drop: {stale}", flush=True)
    for name in stale:
        sql = ci_database.drop_database_sql(name)
        print(f"  -> {sql}", flush=True)
        try:
            con.execute(sql)
        except Exception as exc:
            print(f"     WARNING: DROP failed (best-effort) — {exc}", file=sys.stderr, flush=True)
    con.close()


def _select(args) -> None:
    with open(f"reports/deployment-manifest-{args.head_sha}.json") as f:
        names = modified_names(json.load(f))
    with open("reports/gate2_select.txt", "w") as f:
        if not names:
            print("No artifacts in deployment manifest — skipping dbt run")
        else:
            select_arg = " ".join(names)
            print(f"Selecting models: {select_arg}")
            f.write(select_arg)


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _assemble(args) -> None:
    run_results = results_from_command(
        _load_json(f"{os.environ.get('PROJ', '.')}/target/run_results.json"), "run")
    try:
        with open("reports/gate2_select.txt") as f:
            select_content = f.read().strip()
    except OSError:
        select_content = ""
    dm = _load_json(f"reports/deployment-manifest-{args.head_sha}.json")
    result = gate_2_result.assemble(
        args.db_created.lower() == "true",
        run_results,
        args.head_sha,
        error=gate_2_result.build_crash_error(run_results, select_content),
        manifest_materializations=gate_2_result.materializations_from_deployment_manifest(dm) if dm else {},
        db_name=args.db_name or None,
    )
    os.makedirs("reports", exist_ok=True)
    with open("reports/gate-2.json", "w") as f:
        json.dump(result, f, indent=2)

    passed = result["overall_status"] == "pass"
    runner_io.set_output("passed", "true" if passed else "false")
    # Fail the job outright when the build failed; the post-comment and status
    # steps after this carry `if: always()`, so they still run.
    sys.exit(0 if passed else 1)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    clone = sub.add_parser("clone")
    for flag in ("--pr", "--head-sha", "--domain", "--prod-db"):
        clone.add_argument(flag, required=True)
    clone.set_defaults(func=_clone)
    drop = sub.add_parser("drop-stale")
    for flag in ("--pr", "--db-name", "--domain"):
        drop.add_argument(flag, required=True)
    drop.set_defaults(func=_drop_stale)
    select = sub.add_parser("select")
    select.add_argument("--head-sha", required=True)
    select.set_defaults(func=_select)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--head-sha", required=True)
    assemble.add_argument("--db-created", default="false")
    assemble.add_argument("--db-name", default="")
    assemble.set_defaults(func=_assemble)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
