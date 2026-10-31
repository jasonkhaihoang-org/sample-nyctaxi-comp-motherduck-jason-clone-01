# ingestion/tlc_pipeline.py: loads TLC trips and the zone lookup into `bronze`.
# MotherDuck domain. Its Flight is ingestion/tlc_pipeline.Flight/; orchestration/run_ingest.py runs this file in a Studio Intent.
# Never put credentials or DESTINATION__* config in this file: setup_environment() resolves them.
import os

import dlt
from sources.tlc import tlc_source
from vibedata.dlt.core import dataset
from vibedata.dlt.duckdb import finalize, setup_environment

# CONNECTION_NAME: the dlt source section [sources.<name>] in .dlt/config.toml.
CONNECTION_NAME = "tlc"
# PIPELINE_NAME: the run identity for dlt state, not the connection.
PIPELINE_NAME = "tlc"

# DLT_INGEST_LIMIT limits the items of a safety run or sample load; unset loads everything.
NO_LIMIT = -1
LIMIT = int(os.environ.get("DLT_INGEST_LIMIT", NO_LIMIT))

# Each run reloads the whole fixed window, so every resource is a full replace.
CONTRACT = {"columns": "freeze", "tables": "evolve", "data_type": "freeze"}


def main():
    """Execute the load only when the runner invokes this script."""
    setup_environment()

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination="motherduck",
        dataset_name=dataset("bronze"),
    )

    source = tlc_source.clone(name=CONNECTION_NAME, section=CONNECTION_NAME)()
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
