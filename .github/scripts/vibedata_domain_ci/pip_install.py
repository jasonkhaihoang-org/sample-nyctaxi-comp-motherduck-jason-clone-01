"""Run `pip install`, retrying a failed install with backoff.

An install that pulls in dbt also downloads dbt's parser wheel from a GitHub release, and GitHub's release downloads
fail in short waves (HTTP 504). A failed install is retried; the last attempt's result is returned unchanged, so a
failure that outlasts the retries fails the check with pip's own error. pip's exit code can't tell a
download error from one that never succeeds (an unknown package, a resolver conflict), so those wait ~60 s too.
"""
import subprocess
import time

BACKOFF_S = (4, 8, 16, 32)  # 5 attempts, 60 seconds of waiting in all


def run_pip_install(argv, **kwargs):
    """`subprocess.run(argv, **kwargs)` until it exits 0, at most `len(BACKOFF_S) + 1` times; returns the last CompletedProcess."""
    for wait in (*BACKOFF_S, None):
        result = subprocess.run(argv, **kwargs)
        if result.returncode == 0 or wait is None:
            return result
        print(f"::warning::pip install failed (exit {result.returncode}); retrying in {wait}s")
        time.sleep(wait)
