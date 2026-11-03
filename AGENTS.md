# NYC Taxi Analytics (nyc-taxi-motherduck-demo): Agent Conventions

A DuckDB lakehouse for NYC taxi analytics: real TLC trip records, plus two simulated source systems (fleet operations and master data). Read [`CONTEXT.md`](CONTEXT.md) for the vocabulary.

Read [`repo-map.json`](repo-map.json) first. It says where everything is: layers, entrypoints, commands and artifact locations. This file says how to work.

## Startup

Before a task, read `repo-map.json` and invoke the convention skill for the task. To add a source, invoke [`dlt`](.agents/skills/dlt/SKILL.md); for a model, [`dbt-models`](.agents/skills/dbt-models/SKILL.md). Read other documents only when the task needs them: not `README.md` or `CONTRIBUTING.md` for a pipeline or model change, and never `docs/setup/`, which is repo maintenance. Read `repo-map.json` whole, once, at the start of a task: its `modules`, `artifact_paths` and `sources` are the index of the repo, so do not list directories (`find`, `ls -R`) or read it again in parts. List one folder only when the repo-map names it and the task needs what is in it.

Do not read the installed source code of dbt, dlt or any other library to work out how it behaves. The repo's own models, pipelines and tests show how this repo uses them; for anything else, rely on the library's documented behaviour.

After the conversation is condensed, invoke the [`workarounds`](.agents/skills/workarounds/SKILL.md) skill again before the next tool call: its rules are easy to lose in a summary.

## Medallion layers

- **Bronze**: raw data loaded by dlt (`ingestion/`) into `bronze` (TLC), `ops_raw` and `mdm_raw`.
- **Silver**: dbt staging and intermediate models in `transformation/`.
- **Gold**: dbt marts in `core`, `agg`, `finance` and `ops`.

Layer, schema and builder for each are in `repo-map.json` under `layers`.

## Conventions

Operator conventions are skills in `.agents/skills/`, and the agent's skill list shows each one. Invoke the ones that match your task.

| Skill | Covers |
| --- | --- |
| [`dbt-models`](.agents/skills/dbt-models/SKILL.md) | Layer mapping, model naming, properties files, materialisation |
| [`semantic-model`](.agents/skills/semantic-model/SKILL.md) | Canonical Ossie model shape and VIBEDATA rules |
| [`ontology`](.agents/skills/ontology/SKILL.md) | Business ontology and its mappings: classifying gold tables, concepts, natural identity, relationships, declaration-only |
| [`validating-ontology`](.agents/skills/validating-ontology/SKILL.md) | The ontology's own gate: structure, coverage and content against the model |
| [`validating-semantic-model`](.agents/skills/validating-semantic-model/SKILL.md) | Structural gate plus the content review before commit |
| [`sql-style`](.agents/skills/sql-style/SKILL.md) | SQL formatting |
| [`dbt-testing`](.agents/skills/dbt-testing/SKILL.md) | Generic, singular, unit and Python tests |
| [`dlt`](.agents/skills/dlt/SKILL.md) | Datasets, write disposition, schema contract, bronze carries no logic |
| [`context`](.agents/skills/context/SKILL.md) | What goes into `CONTEXT.md` |
| [`adr`](.agents/skills/adr/SKILL.md) | What goes into an ADR, and when |
| [`workarounds`](.agents/skills/workarounds/SKILL.md) | Temporary rules for platform gaps: single edits of `plan.md` and `verify.md`, running dbt in the sandbox, large files changed by script, verify from the landed table, the Tier-1 dev dataset, sample loads that land whole pages. Each names what removes it |
| [`design-records`](.agents/skills/design-records/SKILL.md) | What goes into a design record |
| [`git-and-prs`](.agents/skills/git-and-prs/SKILL.md) | Commit and pull request format |

## Decisions and designs

- Decisions are ADRs in `docs/adr/`. Standing business answers (week boundary, null handling) are ADRs too: check them before asking a requirement question.
- Each model and pipeline has a design record under `docs/design/`. A design record cites its ADRs as `ADR NNNN`, and an ADR lists the designs it affects.
- Each intent's Requirement, Plan and Verification live where `repo-map.json` `artifact_paths` says (`requirement`, `plan`, `verification`); the plugin names each one for its intent.
- Review findings for triage are in `docs/review/`; do not read them for a build task. Read a proposal in `docs/proposal/` only when the intent's requirement links to it.

## Commands

In a Studio Intent the plugin runs each pipeline on its Flight and dbt on the `dev` target against the Intent's Ephemeral MotherDuck database; the commands below are for a local checkout.

```bash
python3 orchestration/run_all.py          # ingestion, then dbt build
python3 orchestration/run_ingest.py       # dlt pipelines: tlc, ops, mdm
python3 orchestration/run_transform.py    # dbt build
python3 -m pytest tests -q                # Python tests
```

The Python tests need `requirements-dev.txt` installed in the same interpreter (`pip install -r requirements-dev.txt`): the map tests call dbt through `python3 -m dbt.cli.main`, and fail with `No module named 'dbt'` otherwise.

The command for each layer's tests is in `test-map.json`. Lint Python with `ruff check` (the `python_lint` command in `repo-map.json`), which reads `ruff.toml`; do not use the `check_python` tool, which applies rules this repo does not use. Before a push, run `python_tests`, `python_lint`, `sqlfluff lint transformation/models` and the dbt data and unit tests (`dbt_data_tests`, `dbt_unit_tests` in `repo-map.json`).

## Safety

- The Domain's warehouse is the MotherDuck database `sa_prd`, built by the Flights in `ingestion/` and `orchestration/`. A local `orchestration/run_all.py` writes `domain.duckdb` at the repo root instead; it is ignored by git and is never the Domain. Never commit it or downloaded data.
- Never commit secrets. dlt reads them from the bound secret store.
- Do not edit `transformation/profiles.yml` to make a failure pass.

## Maintenance rules

Keep these current in the same change that makes them stale.

| Artifact | Update when | Guard |
| --- | --- | --- |
| `repo-map.json` | A layer, source, pipeline, orchestrator, entrypoint, command or artifact location is added, renamed or removed | `tests/test_maps.py` fails on a missing path, config section or source file, a source no orchestrator runs, or a shared dataset without `produces` |
| `test-map.json` | A layer appears in the repo-map, or a new test starts protecting a layer | `tests/test_maps.py` fails when a layer has no module or a selector selects nothing |
| `CONTEXT.md` | A term appears in, or changes meaning in, a model, ADR or design record. Use `domain-modeling`; do not edit freehand. Typo and link edits are exempt | none |
| `.agents/skills/` | A convention changes | none |
| `AGENTS.md` | A durable fact the code does not show: an environment constraint or a workflow gotcha | none |

