# ingestion/ops_pipeline.Flight/flight.py: Loads the fleet operator's platform into `ops_raw`.
# MotherDuck domain. This file is the pipeline and the Flight: it runs on MotherDuck's compute
# for an Intent run and a schedule alike; only the config differs. The project is fetched at
# GIT_REF and the load runs from the ingestion root, because dlt reads `.dlt/` relative to it.
import json
import os
import sys

import dlt
from dlt.common.libs.sql_alchemy_shims import make_url
from vibedata.dlt.core import dataset
from vibedata.dlt.core.providers.flight_secrets import register_flight_secrets_provider
from vibedata.dlt.duckdb_core import finalize
from vibedata.flight import checkout

GIT_REPO = "accelerate-data/sample-nyctaxi-comp-motherduck-jason-clone"
GIT_REF = os.environ["GIT_REF"]
PROJECT_SUBDIR = "ingestion"
GIT_SECRET_NAME = "nyc_taxi_motherduck_demo_git_auth"
GIT_SECRET_PARAM = "GIT_TOKEN"

# CONNECTION_NAME: the dlt source section [sources.<name>] in .dlt/config.toml.
CONNECTION_NAME = "ops"
# PIPELINE_NAME: the run identity for dlt state, not the connection.
PIPELINE_NAME = "ops"

# Limits the rows of a safety run or sample load; the committed -1 loads everything.
LIMIT = int(os.environ["DLT_INGEST_LIMIT"])
IS_DEV_MODE = os.environ["DEV_MODE"] == "true"

CONTRACT = {"columns": "freeze", "tables": "evolve", "data_type": "freeze"}


def main() -> None:
    os.environ["HOME"] = "/tmp"
    project_dir = checkout(GIT_REPO, PROJECT_SUBDIR, GIT_REF, GIT_SECRET_NAME, GIT_SECRET_PARAM)
    os.chdir(project_dir)
    sys.path.insert(0, project_dir)
    # Source credentials resolve from the Domain's MotherDuck flights secrets.
    register_flight_secrets_provider()

    from sources.ops import ops_source
    from sources.tlc import trip_tables

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        # Load-bearing: any other destination writes a local file and still reports LOAD OK.
        destination="motherduck",
        dataset_name=dataset("ops_raw"),
        dev_mode=IS_DEV_MODE,
    )

    source = ops_source.clone(name=CONNECTION_NAME, section=CONNECTION_NAME)(
        # The operator's records are derived from the yellow trips, read in memory and never written.
        trips=lambda: trip_tables("yellow")
    )
    source.add_limit(LIMIT, count_rows=True)

    # Each run regenerates the whole dataset, so every resource is a full replace.
    for resource in source.selected_resources.values():
        resource.apply_hints(write_disposition="replace", schema_contract=CONTRACT)

    try:
        load_info = pipeline.run(source)
    except Exception as exc:
        finalize(pipeline, error_message=str(exc))
        raise
    print(load_info)
    print("audit:", finalize(pipeline))

    unfinished = [package for package in load_info.load_packages if package.state != "loaded"]
    if load_info.has_failed_jobs or unfinished:
        print("dlt load failed", file=sys.stderr)
        sys.exit(1)

    # The landing gate's destination evidence, from dlt's resolved identity, past the success check.
    try:
        database = make_url(load_info.destination_displayable_credentials).database
    except Exception as exc:
        print("destination-identity unavailable:", exc, file=sys.stderr)
        return
    if not database:
        print("destination-identity unavailable: no database in the resolved identity", file=sys.stderr)
        return
    print("destination-identity:", json.dumps({"type": load_info.destination_type, "database": database}))


if __name__ == "__main__":
    main()
