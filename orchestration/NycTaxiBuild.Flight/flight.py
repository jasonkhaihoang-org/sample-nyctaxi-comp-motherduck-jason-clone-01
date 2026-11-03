# orchestration/NycTaxiBuild.Flight/flight.py: builds and tests the whole dbt project.
# Runs in the MotherDuck Flight runtime: CPython 3.12, dependencies installed by
# uv from the sibling requirements.txt, /tmp writable, git on PATH.
import os
import sys

from dbt.cli.main import dbtRunner
from vibedata.flight import checkout, dbt_run_dir, report_dbt_run

GIT_REPO = "accelerate-data/sample-nyctaxi-comp-motherduck"
GIT_REF = os.environ["GIT_REF"]
PROJECT_SUBDIR = "transformation"
GIT_SECRET_NAME = "nyc_taxi_motherduck_demo_git_auth"
GIT_SECRET_PARAM = "GIT_TOKEN"

COMMANDS = [
    ["deps"],
    ["build", "--target", "flight"],
]


def main() -> None:
    os.environ["HOME"] = "/tmp"
    run_dir = dbt_run_dir()

    project_dir = checkout(GIT_REPO, PROJECT_SUBDIR, GIT_REF, GIT_SECRET_NAME, GIT_SECRET_PARAM)

    for command in COMMANDS:
        result = dbtRunner().invoke(
            [*command, "--project-dir", project_dir, "--profiles-dir", project_dir])
        if not result.success:
            report_dbt_run(run_dir)
            print(f"dbt {command[0]} failed", file=sys.stderr)
            sys.exit(1)
    report_dbt_run(run_dir)
    print("dbt succeeded:", ", ".join(" ".join(command) for command in COMMANDS))


if __name__ == "__main__":
    main()
