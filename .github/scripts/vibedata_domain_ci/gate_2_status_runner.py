"""Thin shell: post the ci/run final status from reports/gate-2.json.

Derives the status from the assembled gate-2 result, not the job's own
conclusion — that only reflects "did some step crash", which stayed 'success'
even on a real dbt build failure. Fails closed on a missing report.

Usage:
    gate_2_status_runner.py --report reports/gate-2.json --sha "$CI_HEAD_SHA" --target-url URL
"""

import argparse
import json
import os

from vibedata_domain_ci import emit_status
from vibedata_domain_ci import gate_2_result

CONTEXT = "ci/run"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--target-url", default="")
    args = parser.parse_args()

    result = None
    try:
        with open(args.report) as f:
            result = json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    state, description = gate_2_result.decide_commit_status(result)
    emit_status.emit_status(os.environ["GITHUB_REPOSITORY"], args.sha, CONTEXT, state, description, args.target_url)


if __name__ == "__main__":
    main()
