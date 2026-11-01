---
name: workarounds
description: "Use after a conversation is condensed, and before editing plan.md or verify.md, running dbt in the sandbox, linting Python, running Tier-1 tests or doing a sample load."
---

# Workarounds
<!-- onboarding
ask: no
reason: A platform content rule or workaround; the same for every domain.
-->

Temporary rules that cover a gap in a platform skill or document. Each names the change that makes it redundant. When that change ships, delete the rule and its row in `AGENTS.md`.

## Write the Plan and the Verification once per phase

Draft the file once. Keep progress and evidence in your head or in a scratch note, and write them into the file in a single edit at the end of the phase. Do not edit the file after each task or check. Each edit echoes a snippet of the file back, and these files are large. When the work comes back on a return, rewrite the file whole in one write; do not patch it section by section.

Remove when: the `planning`, `executing-the-plan` and `verifying` skills write these files once per phase (plugin change).

## Run dbt in the sandbox

The repo's own `profiles.yml` targets are for local and CI use. Do not open it, or `~/.dbt/profiles.yml`, for any reason: not to work out how to run dbt, and not for the shipping contract check, which has nothing to read on this platform (no contracts are published for it). The runtime provides the profile (`DBT_PROFILES_DIR`, `DBT_PROFILE_NAME`) and one target, `dev`, which writes the sandbox file. Run dbt through the runtime wrapper from the dbt project directory:

```bash
cd <dbt project> && <plugin>/scripts/vd-intent-context-run.sh "dbt <command> --target dev"
```

Run `dbt deps` the same way first if `dbt_packages/` is missing. The plain commands in `repo-map.json` `commands` are for a local checkout.

Remove when: the platform's dbt guide in the plugin states this command (plugin change).

## Change large files with a script, not the file editor

The file editor echoes the file back after every edit; for `repo-map.json`, YAML properties files, the Plan and the Verification that is 15K to 27K characters per edit. Change them with a script and print only what you need to confirm:

- `repo-map.json`, `test-map.json`: load with Python `json`, change, dump with `indent=2`, then validate (`python3 -m pytest tests/test_maps.py -q`).
- The Plan and the Verification: append with a heredoc, or replace one block with a short Python `str.replace`.
- YAML properties files (`_sources.yml`, `_staging.yml`): a short Python `str.replace` on a unique anchor.

Never make two edits to the same file in parallel.

Remove when: the editor caps its echo (platform file editor).

## Verify from the landed table and the saved profile

An independent recount at verify reads the landed table and `.agents_tmp/<source>-profile.json`. It never reads the remote source file again.

Remove when: `verifying` says where independent figures come from for an ingestion change (plugin change).

## Tier-1 tests after a safety run

A `DEV_MODE` safety run (the `generating-dlt-pipeline` skill's) loads into a timestamped dev dataset (`bronze_<timestamp>`), printed by the run. Pass that name to the plugin's `scripts/run_bronze_tier1_tests.py --dataset`, not `bronze`. After the full load, pass `bronze`.

Remove when: the Tier-1 runner finds the dev dataset itself (plugin change).

## A sample load lands whole pages, not N rows

`DLT_INGEST_LIMIT` bounds pages, not rows, and dlt does not trim the last page. A file source with row groups lands a whole row group: a Parquet sample load can land about a million rows for a limit of 1,000. Do not write "N rows" for a sample load into a Requirement or Plan, and do not read a larger count as a failed limit. Check the landed count against the source's row-group size instead.

Remove when: the platform's dlt guide in the plugin and `generating-dlt-pipeline` state that the limit bounds pages (plugin change).
