from pathlib import Path
from types import SimpleNamespace

import run_all
import run_ingest
import run_transform

ROOT = Path(__file__).resolve().parents[2]


class Recorder:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def __call__(self, command, cwd, env):
        self.calls.append((list(command), Path(cwd), dict(env)))
        failed = self.fail_on is not None and self.fail_on in " ".join(command)
        return SimpleNamespace(returncode=1 if failed else 0)


def test_ingest_runs_every_pipeline_in_order_from_the_ingestion_root():
    runner = Recorder()
    assert run_ingest.run_ingest(runner) == 0
    assert [Path(c[-1]).name for c, _, _ in runner.calls] == list(run_ingest.PIPELINES)
    assert {cwd for _, cwd, _ in runner.calls} <= {ROOT / "ingestion"}


def test_ingest_environment_points_at_the_repo_database():
    runner = Recorder()
    run_ingest.run_ingest(runner)
    for _, _, env in runner.calls:
        assert env["VD_EPHM_DUCKDB_LOCAL_PATH"] == str(ROOT / "domain.duckdb")
        assert env["VD_DOMAIN_DATA_PLATFORM"] == run_ingest.LOCAL_PLATFORM
        assert env["VD_DOMAIN_SECRET_STORE_KIND"] == "local_toml"


def test_transform_installs_packages_then_builds_against_the_dev_target():
    runner = Recorder()
    assert run_transform.run_transform(runner) == 0
    (deps, deps_cwd, _), (build, build_cwd, env) = runner.calls
    assert deps[-1] == "deps"
    assert build[-3:] == ["build", "--target", "dev"]
    assert deps_cwd == build_cwd == ROOT / "transformation"
    assert env["VD_EPHM_DUCKDB_LOCAL_PATH"] == str(ROOT / "domain.duckdb")


def test_ingest_and_transform_write_to_the_database_they_are_given(tmp_path):
    db = tmp_path / "seed.duckdb"
    runner = Recorder()
    run_ingest.run_ingest(runner, db_path=db)
    run_transform.run_transform(runner, db_path=db)
    assert {env["VD_EPHM_DUCKDB_LOCAL_PATH"] for _, _, env in runner.calls} == {str(db)}


def test_transform_does_not_build_when_package_install_fails():
    runner = Recorder(fail_on="deps")
    assert run_transform.run_transform(runner) == 1
    assert len(runner.calls) == 1


def test_all_does_not_run_dbt_when_ingestion_fails(monkeypatch):
    monkeypatch.setattr(run_ingest, "PIPELINES", ["first_pipeline.py"])
    runner = Recorder(fail_on="first_pipeline.py")
    assert run_all.run_all(runner) == 1
    assert not any("dbt" in " ".join(c) for c, _, _ in runner.calls)
