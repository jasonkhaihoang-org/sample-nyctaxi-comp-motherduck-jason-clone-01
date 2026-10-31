"""Run the dbt project: `dbt deps`, then `dbt build` against the `flight` target, in the Domain's MotherDuck database."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(command, cwd, env):
    return subprocess.run(command, cwd=cwd, env=env, check=False)


DEFAULT_DATABASE = "sa_prd"


def run_transform(runner: Callable = _run, target: str = "flight", database: str = DEFAULT_DATABASE) -> int:
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(ROOT / "transformation")
    env["DBT_PROFILE_NAME"] = "nyc_taxi_analytics"
    # The flight target reads the MotherDuck database from the variable each Flight run sets.
    env["DESTINATION_DATABASE"] = database
    dbt = [sys.executable, "-m", "dbt.cli.main"]
    # packages.yml installs dbt_project_evaluator; a fresh checkout has no dbt_packages/ until deps runs.
    deps = runner([*dbt, "deps"], cwd=ROOT / "transformation", env=env).returncode
    if deps != 0:
        return deps
    return runner([*dbt, "build", "--target", target], cwd=ROOT / "transformation", env=env).returncode


def main() -> int:
    return run_transform()


if __name__ == "__main__":
    raise SystemExit(main())
