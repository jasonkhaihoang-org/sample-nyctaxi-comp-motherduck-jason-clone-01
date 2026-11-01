# ingestion/ops_pipeline.py: loads the fleet operator's platform into `ops_raw`.
# MotherDuck domain. Its Flight is ingestion/ops_pipeline.Flight/; orchestration/run_ingest.py runs this file in a Studio Intent.
# Never put credentials or DESTINATION__* config in this file: setup_environment() resolves them.
import os

import dlt
from sources.ops import ops_source
from sources.tlc import trip_tables
from vibedata.dlt.core import dataset
from vibedata.dlt.duckdb import finalize, setup_environment

# CONNECTION_NAME: the dlt source section [sources.<name>] in .dlt/config.toml.
CONNECTION_NAME = "ops"
# PIPELINE_NAME: the run identity for dlt state, not the connection.
PIPELINE_NAME = "ops"

# DLT_INGEST_LIMIT limits the items of a safety run or sample load; unset loads everything.
NO_LIMIT = -1
LIMIT = int(os.environ.get("DLT_INGEST_LIMIT", NO_LIMIT))

# Each run regenerates the whole operator dataset, so every resource is a full replace.
CONTRACT = {"columns": "freeze", "tables": "evolve", "data_type": "freeze"}


def main():
    """Execute the load only when the runner invokes this script."""
    setup_environment()

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination="motherduck",
        dataset_name=dataset("ops_raw"),
    )

    # The operator's records are derived from the yellow trips. They are read in memory
    # here and never written: this pipeline loads the eight ops_raw tables only.
    source = ops_source.clone(name=CONNECTION_NAME, section=CONNECTION_NAME)(
        trips=lambda: trip_tables("yellow")
    )
    source.add_limit(LIMIT, count_rows=True)

    for resource in source.selected_resources.values():
        resource.apply_hints(write_disposition="replace", schema_contract=CONTRACT)

    try:
        load_info = pipeline.run(source)
    except Exception as exc:
        finalize(pipeline, error_message=str(exc))
        raise
    print(load_info)
    print("audit:", finalize(pipeline))


if __name__ == "__main__":
    main()
