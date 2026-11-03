# Plan: A weekly refresh of the driver models for shift bidding, on the full MotherDuck model-answer Domain

**Goal:** Create `orchestration/DriverWeeklyRefresh.Flight/`, a dbt Flight that rebuilds `agg_driver_daily+` every Monday at 05:00 New York (`0 9 * * 1` UTC), validated and run green once in the sandbox, never activated.

**Requirement:** `docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md`

**Constraints:**
- `NycTaxiBuild.Flight` unchanged; no dlt Flight scheduled.
- `config.json` declares every key with its production value; the sandbox run overrides `DESTINATION_DATABASE`, `DBT_SCHEMA` and `GIT_REF` only; `schedule_cron` is held back on apply.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `DriverWeeklyRefresh` | orchestration | create | `R-01`–`R-05` | `docs/design/orchestration/driver_weekly_refresh.md` | `validate-flight.py orchestration/DriverWeeklyRefresh.Flight --repo-root .`, then a green sandbox run |

**Pipeline rows:**

| Name | Target | Action | Invoked artifacts, in order | Schedule | Reason |
| --- | --- | --- | --- | --- | --- |
| `DriverWeeklyRefresh` | `flight` | `create` | `dbt deps`; `dbt build --select agg_driver_daily+` | `0 9 * * 1` (UTC; Mondays 05:00 New York in EDT, 04:00 in EST) | the weekly shift-bidding refresh, separate from `NycTaxiBuild` |

**Change impact:** no model changes; the Flight reads the released driver models' upstream as the Domain holds it.

## Tasks

### Task 1: `DriverWeeklyRefresh.Flight`

**Requirements:** `R-01`–`R-05` · **Design:** `docs/design/orchestration/driver_weekly_refresh.md` · **Skill:** generating-orchestration · **Depends on:** none

- [x] Generate `flight.py` from the plugin's `flight-dbt.py`, `requirements.txt` and `config.json`; `validate-flight.py`; commit and push
- [x] Sandbox run: rewrite the git secret, apply (`schedule_cron` held back), `run_flight` with the three overrides, until one run is green with the `dbt succeeded:` line
- [x] Confirm `NycTaxiBuild.Flight` unchanged and no Flight left scheduled

## Execution evidence
- Task 1: generated from `motherduck/templates/flight-dbt.py` (repository, project subdirectory, git secret and `--select agg_driver_daily+` filled in), `requirements.txt` from `NycTaxiBuild.Flight` (60 `==` pins), `config.json` with every key's production value and `schedule_cron` `0 9 * * 1`; `validate-flight.py orchestration/DriverWeeklyRefresh.Flight --repo-root .` — exit 0 — 9ea8928.
- Task 1: git secret rewritten (`resolve_creds_and_run.py`, `{{BROKER:github}}`); `create_flight` `DriverWeeklyRefresh` (`0a2a2d45-4d98-4113-af96-7740e4e543f3`, version 1, `schedule_cron` held back: null); `run_flight` run 1 with `DESTINATION_DATABASE=vd_eval_20261103203132_67e8c16b9ef6_eph`, `DBT_SCHEMA=main`, `GIT_REF=intent/new-intent-47c2a273` — SUCCEEDED, exit_code 0; checked out the Intent branch at 9ea8928; `agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard` built, PASS=22 WARN=1 (the existing `assert_semantic_levels_hold` warning); last line `dbt succeeded: deps, build --select agg_driver_daily+`; log `.agents_tmp/driver-weekly-refresh-run.log`.
- Task 1: `NycTaxiBuild.Flight` checksums unchanged; `list_flights` shows no Flight with a schedule.
