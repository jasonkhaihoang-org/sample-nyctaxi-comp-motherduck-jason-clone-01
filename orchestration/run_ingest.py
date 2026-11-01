"""Run the dlt pipelines: tlc, then ops, then mdm, into the Domain's MotherDuck database by default.

The MotherDuck token comes from Studio's credential broker (setup_environment()), so this runs in a Studio
Intent. Production and CI run each pipeline as its Flight, ingestion/<name>_pipeline.Flight/.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ["tlc_pipeline.py", "ops_pipeline.py", "mdm_pipeline.py"]


def _run(command, cwd, env):
    return subprocess.run(command, cwd=cwd, env=env, check=False)


DEFAULT_DATABASE = "sa_prd"


def ingest_environment(database: str = DEFAULT_DATABASE) -> dict[str, str]:
    """The variables vibedata's setup_environment() needs on a MotherDuck domain."""
    env = os.environ.copy()
    env["VD_EPHM_MOTHERDUCK_DATABASE"] = database
    env["VD_DOMAIN_DATA_PLATFORM"] = "motherduck"
    env["VD_DOMAIN_SECRET_STORE_KIND"] = "local_toml"
    return env


def run_ingest(runner: Callable = _run, database: str = DEFAULT_DATABASE) -> int:
    """Run each pipeline from the ingestion root; stop at the first failure and return its code."""
    env = ingest_environment(database)
    for pipeline in PIPELINES:
        result = runner([sys.executable, pipeline], cwd=ROOT / "ingestion", env=env)
        if result.returncode != 0:
            return result.returncode
    return 0


def main() -> int:
    return run_ingest()


if __name__ == "__main__":
    raise SystemExit(main())
