# <Domain name>: Agent Conventions
<!-- onboarding
ask: yes
question: What is this domain for, and where does its data come from?
recommended: One paragraph naming the business area, the source systems and who uses the outputs, in plain words.
alternatives: none; a domain must say what it is.
fills: <Domain name>, <domain paragraph>
-->

<domain paragraph> Read [`CONTEXT.md`](CONTEXT.md) for the vocabulary.

Read [`repo-map.json`](repo-map.json) first. It says where everything is: layers, entrypoints, commands and artifact locations. This file says how to work.

## Startup
<!-- onboarding
ask: no
reason: How agents read this repo; the same for every domain.
-->

Before a task, read `repo-map.json` and invoke the convention skill for the task. To add a source, invoke [`dlt`](.agents/skills/dlt/SKILL.md); for a model, [`dbt-models`](.agents/skills/dbt-models/SKILL.md). Read other documents only when the task needs them: not `README.md` or `CONTRIBUTING.md` for a pipeline or model change. Read `repo-map.json` whole, once, at the start of a task: its `modules`, `artifact_paths` and `sources` are the index of the repo, so do not list directories (`find`, `ls -R`) or read it again in parts.

Do not read the installed source code of dbt, dlt or any other library to work out how it behaves. The repo's own models, pipelines and tests show how this repo uses them; for anything else, rely on the library's documented behaviour.

After the conversation is condensed, invoke the [`workarounds`](.agents/skills/workarounds/SKILL.md) skill again before the next tool call: its rules are easy to lose in a summary.

## Medallion layers
<!-- onboarding
ask: yes
question: Which raw schemas and dbt layers does this domain have?
recommended: One raw schema per source system, named after it; staging → intermediate → marts split by area, starting with core.
alternatives: one raw schema for every source; marts not split by area.
fills: <raw schemas>, <mart areas>
-->

- **Bronze**: raw data loaded by dlt (`ingestion/`) into <raw schemas>.
- **Silver**: dbt staging and intermediate models in `transformation/`.
- **Gold**: dbt marts in <mart areas>.

Layer, schema and builder for each are in `repo-map.json` under `layers`.

## Conventions
<!-- onboarding
ask: no
reason: One row per convention skill written; follows from the skills.
-->

Operator conventions are skills in `.agents/skills/`, and the agent's skill list shows each one. Invoke the ones that match your task.

| Skill | Covers |
| --- | --- |
| [`dbt-models`](.agents/skills/dbt-models/SKILL.md) | Layer mapping, model naming, properties files, materialisation |
| [`sql-style`](.agents/skills/sql-style/SKILL.md) | SQL formatting |
| [`dbt-testing`](.agents/skills/dbt-testing/SKILL.md) | Generic, singular, unit and Python tests |
| [`dlt`](.agents/skills/dlt/SKILL.md) | Datasets, write disposition, schema contract, bronze carries no logic |
| [`context`](.agents/skills/context/SKILL.md) | What goes into `CONTEXT.md` |
| [`adr`](.agents/skills/adr/SKILL.md) | What goes into an ADR, and when |
| [`design-records`](.agents/skills/design-records/SKILL.md) | What goes into a design record |
| [`git-and-prs`](.agents/skills/git-and-prs/SKILL.md) | Commit and pull request format |
| [`workarounds`](.agents/skills/workarounds/SKILL.md) | Temporary rules for platform gaps. Each names what removes it |

## Decisions and designs
<!-- onboarding
ask: yes
question: Where do design records go?
recommended: Layered, `docs/design/models/<layer>/<model>.md`; ADRs, requirements, plans and verifications at the locations repo-map.json artifact_paths declares.
alternatives: flat `docs/design/models/<model>.md`.
fills: the design-record wording here, and repo-map.json artifact_paths.design_record_model
-->

- Decisions are ADRs in `docs/adr/`. Standing business answers are ADRs too: check them before asking a requirement question.
- Each model and pipeline with a decision its code does not explain has a design record under `docs/design/` (models layered by folder). A design record cites its ADRs as `ADR NNNN`, and an ADR lists the designs it affects.
- Each intent's Requirement, Plan and Verification live where `repo-map.json` `artifact_paths` says (`requirement`, `plan`, `verification`); the plugin names each one for its intent.
- Review findings for triage are in `docs/review/`; do not read them for a build task. Read a proposal in `docs/proposal/` only when the intent's requirement links to it.

## Commands
<!-- onboarding
ask: no
reason: The base commands; the same as repo-map.json commands.
-->

<!-- not-a-runnable-fence: a menu of the base commands, run one at a time -->
```bash
python3 orchestration/run_all.py          # ingestion, then dbt build
python3 orchestration/run_ingest.py       # dlt pipelines
python3 orchestration/run_transform.py    # dbt build
python3 -m pytest tests -q                # Python tests
```

The command for each layer's tests is in `test-map.json`. Lint Python with `ruff check` (the `python_lint` command in `repo-map.json`), which reads `ruff.toml`; do not use the `check_python` tool, which applies rules this repo does not use.

## Safety
<!-- onboarding
ask: no
reason: Platform safety; the same for every domain.
-->

- The local warehouse is `domain.duckdb` at the repo root. It is ignored by git and rebuilt by `orchestration/run_all.py`. Never commit it or downloaded data.
- Never commit secrets. dlt reads them from the bound secret store.
- Do not edit `transformation/profiles.yml` to make a failure pass.

## Maintenance rules
<!-- onboarding
ask: no
reason: Keeps the maps honest; the guards are the map tests.
-->

Keep these current in the same change that makes them stale.

| Artifact | Update when | Guard |
| --- | --- | --- |
| `repo-map.json` | A layer, source, pipeline, entrypoint, command or artifact location is added, renamed or removed | `tests/test_maps.py` |
| `test-map.json` | A layer appears in the repo-map, or a new test starts protecting a layer | `tests/test_maps.py` |
| `CONTEXT.md` | A term appears in, or changes meaning in, a model, ADR or design record | none |
| `.agents/skills/` | A convention changes | none |
| `AGENTS.md` | A durable fact the code does not show | none |
