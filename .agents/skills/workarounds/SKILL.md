---
name: workarounds
description: "Use after a conversation is condensed, and before editing plan.md or verify.md, running dbt in the sandbox, linting Python, running Tier-1 tests or doing a sample load."
---

# Workarounds

Temporary rules that cover a gap in a platform skill or document. Each names the change that makes it redundant. When that change ships, delete the rule and its row in `AGENTS.md`. Track whether a rule helped in `docs/setup/skill-changes.md`.

## Write `plan.md` and `verify.md` once per phase

Draft the file once. Keep progress and evidence in your head or in a scratch note, and write them into the file in a single edit at the end of the phase. Do not edit the file after each task or check. Each edit echoes a snippet of the file back, and these files are large. When the work comes back on a return, rewrite the file whole in one write; do not patch it section by section.

Remove when: the `planning`, `executing-the-plan` and `verifying` skills write these files once per phase (`skill-changes.md`).

## Run dbt in the sandbox

The repo's `transformation/profiles.yml` has a `flight` target, the default, which every dbt Flight builds under, and a `dev` target for a local checkout. Do not open it, or `~/.dbt/profiles.yml`, to work out how to run dbt in an Intent, and not for the shipping contract check, which has nothing to read in this repo (it publishes no data contracts). The runtime provides the profile (`DBT_PROFILES_DIR`, `DBT_PROFILE_NAME`) and one target, `dev`, which writes the Intent's Ephemeral MotherDuck database. Run dbt through the runtime wrapper from `transformation/`:

```bash
cd transformation && <plugin>/scripts/vd-intent-context-run.sh "dbt <command> --target dev"
```

Run `dbt deps` the same way first if `dbt_packages/` is missing. The plain commands in `repo-map.json` `commands` are for a local checkout.

Remove when: the platform `duckdb_local/dbt.md` states this command (`skill-changes.md`).

## Change large files with a script, not the file editor

The file editor echoes the file back after every edit; for `repo-map.json`, YAML properties files, `plan.md` and `verify.md` that is 15K to 27K characters per edit. Change them with a script and print only what you need to confirm:

- `repo-map.json`, `test-map.json`: load with Python `json`, change, dump with `indent=2`, then validate (`python3 -m pytest tests/test_maps.py -q`).
- `plan.md`, `verify.md`: append with a heredoc, or replace one block with a short Python `str.replace`.
- YAML properties files (`_sources.yml`, `_staging.yml`) and the canonical model (`logical-model/*.ossie.yaml`): a short Python `str.replace` on a unique anchor. The canonical file is one large single-model document by convention (VD-7126); a targeted editor edit re-emits the whole file.

Never make two edits to the same file in parallel.

Remove when: the editor caps its echo (`skill-changes.md`, platform file editor).

## Verify from the landed table and the saved profile

An independent recount at verify reads the landed table and `.agents_tmp/<source>-profile.json`. It never reads the remote source file again.

Remove when: `verifying` says where independent figures come from for an ingestion change (`skill-changes.md`).

## Tier-1 tests after a safety run

A `DEV_MODE` safety run (the `generating-dlt-pipeline` skill's) loads into a timestamped dev dataset (`bronze_<timestamp>`), printed by the run. Pass that name to the plugin's `scripts/run_bronze_tier1_tests.py --dataset`, not `bronze`. After the full load, pass `bronze`.

Remove when: the Tier-1 runner finds the dev dataset itself (`skill-changes.md`).

## A sample load lands whole pages, not N rows

`DLT_INGEST_LIMIT` bounds pages, not rows, and dlt does not trim the last page. A file source with row groups lands a whole row group: a Parquet sample load can land about a million rows for a limit of 1,000. Do not write "N rows" for a sample load into a Requirement or Plan, and do not read a larger count as a failed limit. Check the landed count against the source's row-group size instead.

Remove when: `duckdb_local/dlt.md` and `generating-dlt-pipeline` state that the limit bounds pages (`skill-changes.md`).

## Regenerate the canonical artifacts by hand after mart changes

`logical-model/*.ossie.yaml` is the hand-authored source of truth (VD-7126); no generator owns it yet. After any mart SQL, `_core.yml`, or `_semantic.yml` change in the same intent, update the canonical in the same intent: physical tables and aliases, added/renamed fields, each LTS `column_map` (an LTS that loses a mapping is disqualified for queries needing it — leave no field supplied by no LTS), each aggregate's `content_levels` and `content_filter` (from its `GROUP BY`, `WHERE` and inner joins) with the holding test, levels, keys and hierarchies (then regenerate `assert_semantic_levels_hold` with `ossie.py level-tests`), each aggregate content level's `key_columns`, metric payloads (`aggregation`, `derived_expression`, `based_on_dimensions`), and SCD validity columns. Then run the skill's `scripts/ossie.py validate` on the canonical file(s) and record the command and exit code. Never commit a mart change with a red validate.
Then the ontology, in the same change: run `scripts/ossie.py refs`, map the concepts the change touched against the dataset it produced, and when the change moves a concept's identity — a grain change, a new SCD, a natural key that became a surrogate — move the concept, its `CONTEXT.md` sentence and every mapping of it together, because a mapping that still resolves to a real field can be wrong about what that field identifies. A new gold mart is not done until `coverage` names it and `refs` accounts for it.

Run `scripts/ossie.py validate` on the canonical file(s) and on `ontology/`, and record each command with its exit code. Never commit a mart change with a red validate.

Remove when: the plugin `generating-ossie-model` skill generates both artifacts, and `generating-dbt-model` carries the update in the same intent (`skill-changes.md`).
