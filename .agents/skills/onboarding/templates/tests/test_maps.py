"""The repo-map and test-map match the repo. Driven by the maps, so it holds from an empty project on."""

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO_MAP = json.loads((ROOT / "repo-map.json").read_text())
TEST_MAP = json.loads((ROOT / "test-map.json").read_text())
DBT_PROJECT = ROOT / REPO_MAP["artifact_paths"]["dbt_project"]
PROFILE = yaml.safe_load((DBT_PROJECT / "dbt_project.yml").read_text())["name"]
# Name the repo's own profile: in the Studio sandbox DBT_PROFILES_DIR and DBT_PROFILE_NAME point at the runtime's.
DBT = [sys.executable, "-m", "dbt.cli.main"]
DBT_PROFILE = ["--profiles-dir", str(DBT_PROJECT), "--profile", PROFILE]
DBT_ENV = {**os.environ, "VD_EPHM_DUCKDB_LOCAL_PATH": str(ROOT / "domain.duckdb")}


def _is_pattern(path: str) -> bool:
    return bool(re.search(r"[{*]", path))


def _literal_paths() -> list[str]:
    paths = [layer["path"] for layer in REPO_MAP["layers"].values() if layer["path"]]
    paths += [runner["path"] for runner in REPO_MAP["orchestrators"].values() if runner.get("path")]
    paths += REPO_MAP["artifact_paths"].values()
    paths += REPO_MAP["entrypoints"].values()
    paths += REPO_MAP["key_directories"].keys()
    paths += [module["path"] for module in REPO_MAP["modules"].values()]
    for source in REPO_MAP["sources"].values():
        paths += [source[k] for k in ("pipeline", "docs", "module", "tests", "design_record") if k in source]
    return [p for p in paths if not _is_pattern(p)]


def test_repo_map_validates_against_its_schema():
    schema = json.loads((ROOT / "repo-map.schema.json").read_text())
    jsonschema.validate(REPO_MAP, schema)


def test_every_layer_has_one_builder():
    assert {layer["built_by"] for layer in REPO_MAP["layers"].values()} <= {"dlt", "dbt", "custom"}


def test_orchestrators_and_sources_agree():
    declared = set(REPO_MAP["sources"])
    runs = {name for runner in REPO_MAP["orchestrators"].values() for name in runner["runs"]}
    assert declared - runs == set(), f"sources no orchestrator runs: {sorted(declared - runs)}"
    assert runs - declared == set(), f"orchestrators run unknown sources: {sorted(runs - declared)}"


def test_a_shared_dataset_declares_what_each_pipeline_lands():
    by_dataset = {}
    for name, source in REPO_MAP["sources"].items():
        by_dataset.setdefault(source["dataset"], []).append(name)
    for dataset, names in by_dataset.items():
        if len(names) < 2:
            continue
        claimed = []
        for name in names:
            tables = REPO_MAP["sources"][name].get("produces")
            assert tables, f"{name} shares dataset {dataset} but declares no produces"
            assert all(t.strip() for t in tables), f"{name} declares a blank table name"
            claimed += tables
        assert len(claimed) == len(set(claimed)), (
            f"sources on {dataset} claim the same table: {sorted(claimed)}"
        )


RESOURCE_IN_MODULE = re.compile(r"dlt\.resource\(", re.M)
PIPELINES_IN_CODE = re.compile(r"^PIPELINES\s*(?::[^=\n]*)?=\s*\[(.*?)\]", re.S | re.M)


def test_every_source_declares_or_exposes_its_tables():
    """A source with no `produces` must still land something: its module has to declare a resource."""
    for name, source in REPO_MAP["sources"].items():
        if source.get("produces"):
            continue
        module = (ROOT / source["module"]).read_text()
        assert RESOURCE_IN_MODULE.search(module), (
            f"{name} declares no produces and its module declares no dlt resource"
        )


def test_an_orchestrator_runs_what_its_code_runs():
    """A source added to `runs` but not to the runner's list never runs, and no other test sees it."""
    for name, runner in REPO_MAP["orchestrators"].items():
        if "path" not in runner:
            continue  # a runner outside the repo only declares what it starts
        runner_path = ROOT / runner["path"]
        assert runner_path.exists(), f"{name}: runner path does not exist: {runner['path']}"
        match = PIPELINES_IN_CODE.search(runner_path.read_text())
        assert match, f"{name}: no literal PIPELINES list to compare against"
        in_code = {
            item.strip().strip("\"'").removesuffix("_pipeline.py")
            for item in match.group(1).split(",")
            if item.strip()
        }
        assert in_code == set(runner["runs"]), (
            f"{name}: code runs {sorted(in_code)}, map says {sorted(runner['runs'])}"
        )


def test_repo_map_paths_exist():
    assert [p for p in _literal_paths() if not (ROOT / p).exists()] == []


def test_every_source_is_registered_in_the_dlt_config():
    config = tomllib.loads((ROOT / REPO_MAP["artifact_paths"]["source_config"]).read_text())
    for name, source in REPO_MAP["sources"].items():
        section = config
        for key in source["config_section"].split("."):
            section = section.get(key, {})
        assert section, f"{name}: [{source['config_section']}] missing"


def test_test_map_paths_exist():
    missing = []
    for name, module in TEST_MAP["modules"].items():
        for key in ("sources", "unit", "data", "structural"):
            missing += [f"{name}.{key}: {p}" for p in module.get(key, []) if not (ROOT / p).exists()]
    assert missing == []


CI_RULE_KEYS = {"role", "paths", "checks", "all"}


def test_test_map_ci_section_is_rules_over_roles():
    """CI reads only `ci`, never `modules`: each rule names a role or paths, and the checks they run."""
    ci = TEST_MAP.get("ci")
    assert ci is not None, "test-map.json has no ci section"
    assert ci.get("version") == 1 and ci.get("rules"), "the ci section needs version 1 and its rules"
    for rule in ci["rules"]:
        assert set(rule) <= CI_RULE_KEYS, f"unknown keys in ci rule {rule}"
        assert "role" in rule or "paths" in rule, f"ci rule names neither a role nor paths: {rule}"
        assert isinstance(rule["checks"], list), f"ci rule has no checks list: {rule}"


def test_a_ci_rule_with_paths_names_a_folder_role():
    """A rule's paths sit under its role's folder, so a role a rule narrows must end in `/`."""
    roles = REPO_MAP["artifact_paths"]
    narrowed = {rule["role"] for rule in TEST_MAP.get("ci", {}).get("rules", []) if "role" in rule and "paths" in rule}
    assert [r for r in sorted(narrowed) if r in roles and not roles[r].endswith("/")] == []


def test_dbt_sources_name_a_schema_and_never_a_catalog():
    path = ROOT / REPO_MAP["artifact_paths"]["dbt_sources"]
    sources = (yaml.safe_load(path.read_text()) or {}).get("sources") or []
    assert [s["name"] for s in sources if "database" in s] == []
    assert [s["name"] for s in sources if "{{" in str(s.get("schema", ""))] == []


def test_ref_and_source_render_without_a_catalog():
    """A view that stores a catalog breaks in the sandbox, a renamed copy of the Domain file."""
    text = (DBT_PROJECT / "macros/relations.sql").read_text()
    assert "macro ref()" in text and "macro source()" in text
    assert text.count("include(database=False)") == 2


@pytest.fixture(scope="session")
def dbt_packages():
    if not (DBT_PROJECT / "dbt_packages").exists():
        subprocess.run([*DBT, "deps", *DBT_PROFILE], cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, check=True)


def test_dbt_project_parses(dbt_packages):
    subprocess.run([*DBT, "parse", *DBT_PROFILE], cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, check=True)


DBT_SELECTORS = [
    (name, kind, module["selectors"][kind])
    for name, module in TEST_MAP["modules"].items()
    for kind in ("data", "unit")
    if kind in module.get("selectors", {})
]


@pytest.mark.parametrize("name,kind,select", DBT_SELECTORS, ids=lambda v: str(v))
def test_test_map_dbt_selectors_resolve_to_at_least_one_test(dbt_packages, name, kind, select):
    command = [*DBT, "ls", *DBT_PROFILE, "--select", select, "--resource-type", "unit_test" if kind == "unit" else "test"]
    if kind == "data":
        command += ["--exclude", "test_type:unit"]
    out = subprocess.run(command, cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, text=True, check=True).stdout
    assert [line for line in out.splitlines() if ":" in line and not line.startswith(" ")], f"{name}.{kind} selects nothing"
