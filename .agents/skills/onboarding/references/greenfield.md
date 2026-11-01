# Greenfield

The repo has no dbt project and no pipelines, and the Domain database is empty. Onboarding sets up an empty, working project so the first intent is a plain "add a source".

## Requirement

Ask what the domain is for and where its data will come from. Scope: the whole repo.

## Design: grill by file and section

Use the `grilling` skill. Every template under [templates/](../templates/) marks each section with an `<!-- onboarding -->` block:

- `ask: yes`: a question, a recommended answer and the alternatives. Ask these.
- `ask: no`: platform-driven, with the reason. Show them, do not ask.

Go file by file, in this order: `AGENTS.md`, then the `dbt-models`, `dlt`, `dbt-testing`, `sql-style` and `git-and-prs` skills, then the content skills and `workarounds`. For each file, show every section's recommended text in one message and ask its `ask: yes` sections one at a time, recommendation first; the user may also override an `ask: no` section. A section answered once (for example the layers, in `AGENTS.md` and [`dbt-models.md`](../templates/skills/dbt-models.md)) is not asked again.

Also ask the dbt project name (recommended: the domain slug with underscores), and ask for the Domain's first business terms as their own question; pass the user's answer, not terms you drew from the purpose, to `domain-modeling` for `CONTEXT.md`.

## Build

Write from [templates/](../templates/), filling the confirmed answers. Every platform gets the same files; the only platform difference is the roles in the table below. Start each map by copying its template file, never by retyping it, then set `generated_at` and add what the answers add. Copy `profiles.yml` as it is on every platform: it is the local profile for local runs, never a target on the Domain's platform, and a Studio Intent supplies its own profile. Never write a profile that names a platform adapter or an Intent coordinate. Keep the template's `test-map.json` `modules` as they are, and keep its `ci` section exactly: never add, remove or edit a rule, even one over a role the repo does not define, which simply never matches.

| Write | From |
| --- | --- |
| `transformation/dbt_project.yml`, `packages.yml`, `profiles.yml` | `templates/dbt/` |
| `transformation/macros/relations.sql`, `generate_schema_name.sql` | `templates/dbt/` |
| `transformation/models/<layer>/` per confirmed layer, `models/staging/_sources.yml` (`version: 2`, no sources), `transformation/tests/` | empty, with a `.gitkeep` where a folder would be empty |
| `ingestion/.dlt/config.toml`, `ingestion/sources/`, `ingestion/requirements.txt` | `templates/dlt/` |
| `tests/conftest.py`, `tests/orchestration/test_run.py` | `templates/tests/` (`test_run.py` goes under `tests/orchestration/`) |
| `orchestration/run_ingest.py`, `run_transform.py`, `run_all.py` | `templates/orchestration/` |
| `tests/test_maps.py`, `tests/test_adr_links.py` | `templates/tests/` |
| Where the repo checks run | The Repo checks question in [base-setup.md](base-setup.md); recommended `.github/workflows/repo-checks.yml` from `templates/repo/` |
| `repo-map.json`, `repo-map.schema.json`, `test-map.json` | `templates/repo/`, layers from the answers, `sources` empty, each role in `## Repo-map roles` of `../../../_shared/platforms/<platform>/ci.md` set to that path, and the `ci` section as the template has it |
| `AGENTS.md`, `ruff.toml`, `requirements-dev.txt`, `.gitignore` (`gitignore-fragment`) | `templates/repo/`, `<!-- onboarding -->` blocks removed |
| `.sqlfluff` | `templates/repo/sqlfluff.cfg`; its profile comes from `.github/profiles/`, which `install-ci` writes |
| `docs/adr/`, `docs/review/`, `docs/proposal/` | empty, with a `.gitkeep` |
| `contracts/`, `.agents/skills/data-contract/`, `.agents/skills/validating-data-contract/` | `contracts/` empty with a `.gitkeep`; both skills seeded with their `scripts/`, by the Convention skills paragraph in [base-setup.md](base-setup.md). Declared in both maps, so the first contract has its path |
| `.agents/skills/<name>/SKILL.md`, one per convention skill | `templates/skills/<name>.md`, with the confirmed answers in place of the placeholders and every `<!-- onboarding -->` block removed |
| `CONTEXT.md` and any ADR a confirmed decision earns | `domain-modeling` |
| CI, `.github/profiles/`, `.github/scripts/adr_lint.py` | `install-ci`. Not optional: `.sqlfluff` and the `adr_lint` command depend on it |

Fill the placeholders:

| Placeholder | Value |
| --- | --- |
| `<project_name>` | The confirmed dbt project name, in `dbt_project.yml`, `profiles.yml` and `run_transform.py` |
| `<Domain name>`, `<domain paragraph>` | The requirement answer |
| `<domain slug>`, `<one line>` | `repo-map.json` `applications`: the slug and the domain paragraph's first sentence |
| `<raw schema>`, `<source system>` | `repo-map.json` `layers`: one entry per confirmed raw schema, keyed by its name, `path` `ingestion/` |
| mart areas | One `layers` entry and one `dbt_project.yml` block under `marts` per confirmed area, path `transformation/models/marts/<area>/` |
| Ossie document | Not created at greenfield: there is no fact to model yet. The first intent that lands a fact-bearing mart creates `logical-model/` with the `semantic-model` skill, registers it in `repo-map.json` and `test-map.json`, and validates it before shipping |
| `<UTC timestamp>` | The time of writing, in both maps |
| `<local platform>` | In `orchestration/run_ingest.py`: the Domain's platform kind, as the Intent facts give it, which local runs load into |
| `orchestrators` | Keep the `run_ingest` entry the template ships (`kind: python`, `path: orchestration/run_ingest.py`, `runs: []`). The first source adds itself to `runs` and to `PIPELINES`; a runner outside the repo is a separate entry with `location` |

Write no source, pipeline, model, contract or design record: the first intent adds them, and a contract with the first relation that lands. Write no review file: there is nothing to review, and `reverse` has nothing to draft.

## Verify

Check the CI roles and the `ci` section against the templates with the onboarded-repo plan, from the repository root:

```bash
SKILL_DIR="<this skill's directory>" \
  && python3 "$SKILL_DIR/scripts/merge_maps.py" plan --repo . --platform <platform>
```

Substitute this skill's directory for `$SKILL_DIR` and the Domain's platform kind for `<platform>`. Its `repo-map.json` `add` and `differs_from_template` are both empty and `ci_matches_default` is true; otherwise set the role or copy the section it names, and run it again.

Install `requirements-dev.txt`. The base commands pass on the empty project: `dbt deps`, `dbt parse`, `python3 -m pytest tests -q`, `ruff check .`. `dbt parse` warns that the layer config paths match no models: expected until each layer has its first model; do not remove the blocks. Then the dry run, with one task: add the first source.

## Ship

One PR. The commit body and the PR description list the confirmed answers, one line per section, and recommend the next intent: add the first source.
