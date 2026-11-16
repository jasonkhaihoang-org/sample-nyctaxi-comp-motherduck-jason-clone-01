"""Thin shell: run the MotherDuck Gate 3 (ci/unit-tests) dbt unit tests.

Selects the unit tests of every model in reports/deployment-manifest-<sha>.json,
runs `dbt test`, has parse_run_results.py write reports/gate-3.json, then adds
the modified models and marks a zero-test run as skipped. Exits with the
parser's code. An empty closure writes a zero-count pass without running dbt.

Usage:
    gate_3_unit_runner.py --head-sha "$HEAD_SHA"
"""

import argparse
import json
import os
import subprocess
import sys

from vibedata_domain_ci.write_modified_json import modified_names


def unit_test_selector(names: list[str]) -> str:
    # Space separates union selectors: each "{n},test_type:unit" is the AND
    # of that model with unit tests — mirrors gate3_fabric_runner.py's
    # selector pattern. A single comma-joined string would instead
    # intersect all names together, matching no node once names has 2+
    # entries.
    return " ".join(f"{n},test_type:unit" for n in names)


def augment_summary(summary: dict, names: list[str]) -> dict:
    """Add modified_models for coverage reporting; zero tests run is a skip, not a vacuous pass (a crash stays an error)."""
    out = {**summary, "modified_models": names}
    if out.get("total", 0) == 0 and out.get("overall_status") != "error":
        out["overall_status"] = "skipped"
    return out


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args(argv)

    # HEAD_SHA_SHORT required by dbt_motherduck_ci profile (md:pr_<N>_<sha>).
    os.environ["HEAD_SHA_SHORT"] = args.head_sha[:7]
    proj = os.environ.get("PROJ", ".")

    with open(f"reports/deployment-manifest-{args.head_sha}.json") as f:
        names = modified_names(json.load(f))

    if not names:
        with open("reports/gate-3.json", "w") as f:
            json.dump({"overall_status": "pass", "counts": {"pass": 0, "fail": 0, "error": 0, "skip": 0}, "tests": [], "failures": [], "modified_models": []}, f)
        print("Gate 3: no models in closure — skipping unit tests.")
        sys.exit(0)

    subprocess.run([
        "dbt", "test",
        "--project-dir", proj,
        "--select", unit_test_selector(names),
        "--profiles-dir", ".github/profiles",
        "--profile", "dbt_motherduck_ci",
        "--target", "ci",
        "--quiet",
    ])

    # parse_run_results.py writes gate-3.json and exits 0 (pass) or 1 (fail).
    rc = subprocess.run([
        sys.executable, "-m", "vibedata_domain_ci.parse_run_results",
        "--input", f"{proj}/target/run_results.json",
        "--output", "reports/gate-3.json",
        "--command", "test",
    ]).returncode

    try:
        with open("reports/gate-3.json") as f:
            summary = json.load(f)
        with open("reports/gate-3.json", "w") as f:
            json.dump(augment_summary(summary, names), f)
    except (OSError, json.JSONDecodeError):
        pass

    sys.exit(rc)


if __name__ == "__main__":
    main()
