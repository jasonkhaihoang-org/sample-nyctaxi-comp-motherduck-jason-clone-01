import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO_MAP = json.loads((ROOT / "repo-map.json").read_text())
TEST_MAP = json.loads((ROOT / "test-map.json").read_text())


def _exists(path: str) -> bool:
    """A path with a {placeholder} is checked up to the last whole directory before it."""
    prefix = re.split(r"[{*]", path)[0]
    static = prefix.rstrip("/") if prefix.endswith("/") or "/" not in prefix else prefix.rsplit("/", 1)[0]
    return (ROOT / static).exists() if static else True


def test_repo_map_validates_against_its_schema():
    schema = json.loads((ROOT / "repo-map.schema.json").read_text())
    jsonschema.validate(REPO_MAP, schema)


def test_repo_map_names_every_layer_with_one_builder():
    assert set(REPO_MAP["layers"]) == {
        "bronze", "staging", "intermediate", "core", "agg", "finance", "ops", "ops_raw", "mdm_raw", "seeds",
    }
    assert {layer["built_by"] for layer in REPO_MAP["layers"].values()} <= {"dlt", "dbt", "custom"}


def test_repo_map_paths_exist():
    paths = [layer["path"] for layer in REPO_MAP["layers"].values() if layer["path"]]
    paths += [runner["path"] for runner in REPO_MAP["orchestrators"].values() if runner.get("path")]
    paths += REPO_MAP["artifact_paths"].values()
    paths += REPO_MAP["entrypoints"].values()
    paths += REPO_MAP["key_directories"].keys()
    paths += [m["path"] for m in REPO_MAP["modules"].values()]
    for source in REPO_MAP["sources"].values():
        paths += [source[k] for k in ("pipeline", "docs", "module", "tests", "design_record")]
    missing = [p for p in paths if not _exists(p)]
    assert missing == []


def test_every_source_is_registered_in_the_dlt_config():
    config = tomllib.loads((ROOT / "ingestion" / ".dlt" / "config.toml").read_text())
    for name, source in REPO_MAP["sources"].items():
        assert source["config_section"] == f"sources.{name}"
        assert name in config["sources"], f"{name} has no [sources.{name}] section"


def test_every_layer_has_a_test_map_module():
    modules = set(TEST_MAP["modules"])
    for name, layer in REPO_MAP["layers"].items():
        if layer["built_by"] == "custom":
            continue  # no skill has a procedure for it, so no test module is expected
        expected = "ingestion" if layer["built_by"] == "dlt" else name
        assert expected in modules, f"layer {name} has no test-map module {expected}"


def test_the_ontology_is_declared_and_gated():
    """Every repo has an ontology beside its glossary, whatever its layers."""
    assert REPO_MAP["artifact_paths"]["ontology"].startswith("ontology/")
    assert REPO_MAP["artifact_paths"]["ontology_mapping"].startswith("ontology/")
    assert "ontology" in REPO_MAP["modules"], "the ontology module has no path"
    assert (ROOT / "CONTEXT.md").exists(), "an ontology without a glossary has no source"
    gate = TEST_MAP["modules"].get("ontology", {}).get("commands", {}).get("structural", "")
    assert "validate ontology" in gate and "refs ontology" in gate, gate
    assert (ROOT / ".agents/skills/validating-ontology/SKILL.md").exists(), \
        "the ontology has no validation skill of its own"


def test_source_artifact_patterns_resolve_for_every_source():
    for name in REPO_MAP["sources"]:
        for key in ("source_module", "source_tests", "pipeline", "resource_docs", "design_record_pipeline"):
            pattern = REPO_MAP["artifact_paths"][key]
            path = pattern.format(name=name, connection=name, pipeline=name)
            assert (ROOT / path).exists(), f"{key} for {name}: {path}"


def test_every_dlt_layer_has_a_source():
    datasets = {s["dataset"] for s in REPO_MAP["sources"].values()}
    dlt_schemas = {layer["schema"] for layer in REPO_MAP["layers"].values() if layer["built_by"] == "dlt"}
    assert datasets == dlt_schemas


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


def test_test_map_paths_exist():
    missing = []
    for name, module in TEST_MAP["modules"].items():
        for key in ("sources", "unit", "data"):
            missing += [f"{name}.{key}: {p}" for p in module.get(key, []) if not _exists(p)]
    assert missing == []


DBT_PROJECT = ROOT / "transformation"
# The repo's own profile and its local target, named explicitly: in the Studio sandbox
# DBT_PROFILES_DIR and DBT_PROFILE_NAME point at the runtime profile, which plain `dbt ls`
# would otherwise use, and the profile's default target is the Flights' MotherDuck one,
# which these offline tests must never open.
DBT = [sys.executable, "-m", "dbt.cli.main"]
DBT_PROFILE = ["--profiles-dir", str(DBT_PROJECT), "--profile", "nyc_taxi_analytics", "--target", "dev"]
# The profile reads its path from the sandbox variable; parsing never opens the file.
DBT_ENV = {**os.environ, "VD_EPHM_DUCKDB_LOCAL_PATH": str(ROOT / "domain.duckdb")}


@pytest.fixture(scope="session")
def dbt_packages():
    """Install packages.yml once on a fresh checkout; `dbt ls` refuses to run without them."""
    if not (DBT_PROJECT / "dbt_packages").exists():
        subprocess.run([*DBT, "deps", *DBT_PROFILE], cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, check=True)


def _dbt_ls(select: str, resource_type: str, exclude: str | None = None) -> list[str]:
    command = [*DBT, "ls", *DBT_PROFILE, "--select", select, "--resource-type", resource_type]
    if exclude:
        command += ["--exclude", exclude]
    out = subprocess.run(command, cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if ":" in line and not line.startswith(" ")]


DBT_SELECTORS = [
    (name, kind, module["selectors"][kind])
    for name, module in TEST_MAP["modules"].items()
    for kind in ("data", "unit")
    if kind in module.get("selectors", {})
]


@pytest.mark.parametrize("name,kind,select", DBT_SELECTORS, ids=lambda v: str(v))
def test_test_map_dbt_selectors_resolve_to_at_least_one_test(dbt_packages, name, kind, select):
    if kind == "unit":
        nodes = _dbt_ls(select, "unit_test")
    else:
        nodes = _dbt_ls(select, "test", exclude="test_type:unit")
    assert nodes, f"{name}.{kind}: `{select}` selects no tests"


REVIEW_STATUS = re.compile(r"^(open|intent|deferred|declined: .+|proposal → P-\d{4})$")
PROPOSAL_STATUS = re.compile(r"^(proposed|accepted|rejected|in-intent: .+|shipped: .+)$")


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name} has no frontmatter"
    block = text.split("---\n", 2)[1]
    return dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)


def _review_rows(path: Path) -> list[list[str]]:
    rows = [line.strip("|").split("|") for line in path.read_text().splitlines() if line.startswith("| R-")]
    return [[cell.strip() for cell in row] for row in rows]


def test_review_and_proposal_paths_are_declared():
    assert REPO_MAP["artifact_paths"]["review"] == "docs/review/{date}-{type}-{slug}.md"
    assert REPO_MAP["artifact_paths"]["proposal"] == "docs/proposal/{nnnn}-{slug}.md"


def test_every_review_has_frontmatter_and_a_valid_status_per_finding():
    reviews = sorted((ROOT / "docs/review").glob("*.md"))
    assert reviews
    for review in reviews:
        meta = _frontmatter(review)
        assert {"type", "date", "commit", "source"} <= meta.keys(), review.name
        assert review.name.startswith(f"{meta['date']}-{meta['type']}-"), review.name
        rows = _review_rows(review)
        assert rows, review.name
        for row in rows:
            assert row[1] in {"platform", "convention", "bug", "gap", "style"}, (review.name, row[0])
            assert REVIEW_STATUS.match(row[-1]), (review.name, row[0], row[-1])


def test_proposals_and_review_findings_point_at_each_other():
    proposals = {p.name[:4]: p for p in (ROOT / "docs/proposal").glob("[0-9][0-9][0-9][0-9]-*.md")}
    assert proposals
    findings = {}
    for review in (ROOT / "docs/review").glob("*.md"):
        for row in _review_rows(review):
            findings[(review.stem, row[0])] = row[-1]
    for number, proposal in proposals.items():
        meta = _frontmatter(proposal)
        assert PROPOSAL_STATUS.match(meta["status"]), proposal.name
        for ref in filter(None, meta.get("findings", "").strip("[]").split(",")):
            review, finding = ref.strip().split("#")
            assert findings.get((review, finding)) == f"proposal → P-{number}", (proposal.name, ref)
    for (review, finding), status in findings.items():
        if status.startswith("proposal → "):
            assert status[-4:] in proposals, (review, finding)


def test_dbt_sources_name_a_schema_and_never_a_catalog():
    """The Studio sandbox is a renamed copy of the domain file, so a source's catalog never resolves there."""
    import yaml

    sources = yaml.safe_load((ROOT / REPO_MAP["artifact_paths"]["dbt_sources"]).read_text())["sources"]
    assert [s["name"] for s in sources if "database" in s] == []
    assert [s["name"] for s in sources if "{{" in str(s.get("schema", ""))] == []


def test_compiled_references_name_no_catalog(dbt_packages):
    """macros/relations.sql: a view that stores a catalog breaks in the renamed sandbox copy."""
    subprocess.run(
        [*DBT, "compile", *DBT_PROFILE, "--select", "int_trips_enriched"],
        cwd=DBT_PROJECT, env=DBT_ENV, capture_output=True, check=True,
    )
    compiled = next((DBT_PROJECT / "target/compiled").rglob("int_trips_enriched.sql")).read_text()
    assert '"intermediate"."int_trips_conformed"' in compiled
    assert not re.search(r'"[^"]+"\."intermediate"\."int_trips_conformed"', compiled)
