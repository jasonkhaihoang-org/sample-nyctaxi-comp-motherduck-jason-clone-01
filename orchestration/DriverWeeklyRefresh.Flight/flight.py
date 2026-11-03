# orchestration/DriverWeeklyRefresh.Flight/flight.py: rebuilds the driver models (agg_driver_daily and
# everything downstream of it) every Monday for shift bidding. No ingestion: the daily refresh loads the sources.
#
# Runs in the MotherDuck Flight runtime: CPython 3.12, dependencies installed by
# uv from the sibling requirements.txt, /tmp writable, git on PATH.
#
import os
import sys

from dbt.cli.main import dbtRunner
from vibedata.flight import checkout, dbt_run_dir, report_dbt_run

GIT_REPO = "accelerate-data/sample-nyctaxi-comp-motherduck"
GIT_REF = os.environ["GIT_REF"]
PROJECT_SUBDIR = "transformation"
GIT_SECRET_NAME = "nyc_taxi_motherduck_demo_git_auth"
GIT_SECRET_PARAM = "GIT_TOKEN"

# DBT_EMPTY_RUN is a config.json key, committed "false"; a CI smoke run overrides it. It arrives
# as a string, and an unrecognised one fails rather than quietly running the full build.
TRUE_VALUES = ("1", "true", "yes", "on")
FALSE_VALUES = ("", "0", "false", "no", "off")
EMPTY_COMMANDS = ("build", "run")

COMMANDS = [
    ["deps"],
    ["build", "--select", "agg_driver_daily+"],
]


def empty_run(raw: str) -> bool:
    value = raw.strip().lower()
    if value not in TRUE_VALUES + FALSE_VALUES:
        raise SystemExit(f"DBT_EMPTY_RUN {raw!r} is not a boolean (true/false, 1/0).")
    return value in TRUE_VALUES


def with_empty(command: list[str], empty: bool) -> list[str]:
    return [*command, "--empty"] if empty and command[0] in EMPTY_COMMANDS else command


def main() -> None:
    os.environ["HOME"] = "/tmp"
    empty = empty_run(os.environ.get("DBT_EMPTY_RUN", "false"))
    run_dir = dbt_run_dir()

    project_dir = checkout(GIT_REPO, PROJECT_SUBDIR, GIT_REF, GIT_SECRET_NAME, GIT_SECRET_PARAM)

    commands = [with_empty(command, empty) for command in COMMANDS]
    for command in commands:
        result = dbtRunner().invoke(
            [*command, "--project-dir", project_dir, "--profiles-dir", project_dir])
        if not result.success:
            report_dbt_run(run_dir)
            print(f"dbt {command[0]} failed", file=sys.stderr)
            sys.exit(1)
    report_dbt_run(run_dir)
    print("dbt succeeded:", ", ".join(" ".join(command) for command in commands))


if __name__ == "__main__":
    main()
