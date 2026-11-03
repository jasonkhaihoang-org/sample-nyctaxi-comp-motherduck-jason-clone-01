# Verification: A weekly refresh of the driver models for shift bidding, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `c6468fb`: `orchestration/DriverWeeklyRefresh.Flight/` is a new dbt Flight beside an unchanged `NycTaxiBuild.Flight`. It passes its validator and ran green once in the sandbox, building `agg_driver_daily+` in the Intent's Ephemeral database at the Intent branch. Its `schedule_cron` `0 9 * * 1` (UTC) is committed, not activated. Limits: a Flight cron is UTC, so the refresh runs at 05:00 New York during daylight saving and 04:00 in winter (recorded as decided); the schedule does nothing until customer CI/CD deploys it on a Business plan.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` a new Flight beside an unchanged `NycTaxiBuild.Flight` | `ls orchestration/`; `sha256sum orchestration/NycTaxiBuild.Flight/*` against Discovery | `DriverWeeklyRefresh.Flight` added (action `create`); the three checksums equal | `c6468fb` |
| `R-02` no ingestion, `agg_driver_daily+` | `flight.py` read against the plugin template; the run's log | `COMMANDS` are `deps` and `build --select agg_driver_daily+`, no dlt import; the run built exactly `agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard` and their tests | `c6468fb` |
| `R-03` Mondays 05:00 New York, never activated | `config.json` `schedule_cron`; `list_flights` | `0 9 * * 1` = 05:00 EDT (09:00 − 4 h) and 04:00 EST (09:00 − 5 h); every Flight's `schedule_cron` null in the account | `c6468fb` |
| `R-04` validator and one green run | `validate-flight.py orchestration/DriverWeeklyRefresh.Flight --repo-root .`; `get_flight_run` / `get_flight_logs` of run 1 | exit 0; SUCCEEDED, exit_code 0, `dbt succeeded: deps, build --select agg_driver_daily+` | `c6468fb` |
| `R-05` nothing in `sa_prd` | run 1's recorded config | `DESTINATION_DATABASE=vd_eval_20261103203132_67e8c16b9ef6_eph` (the `flight` target's database), `DBT_SCHEMA=main`, `GIT_REF=intent/new-intent-47c2a273`; no schedule activated | `c6468fb` |
| `DriverWeeklyRefresh` (`create`) | the gates below | pass | `c6468fb` |

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Native validation | `python3 <plugin>/scripts/platforms/motherduck/validate-flight.py orchestration/DriverWeeklyRefresh.Flight --repo-root .` | 0 | pass |
| Ephemeral run evidence | run 1 of `DriverWeeklyRefresh` (`0a2a2d45-4d98-4113-af96-7740e4e543f3`, version 1) | 0 | SUCCEEDED, exit_code 0, PASS=22 WARN=1 (the existing `assert_semantic_levels_hold` warning), the `dbt succeeded:` line |
| `generating-orchestration` audit | the `create` row's checks | — | validator 0; every invoked artifact resolves (`dbt ls --select agg_driver_daily+` lists three models); run evidence present; no finding |
| Existing Flight unchanged | `sha256sum orchestration/NycTaxiBuild.Flight/*` | 0 | equal |
| Scope | `git diff --name-only 7fcde94 HEAD` | 0 | the new Flight's three files and docs only; no model changed |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | fresh |
| Contract promotion | — | — | not applicable: no dbt model touched |
| Orchestration documentation | `README.md` § Weekly driver refresh, from `flight.py`, `config.json` and the design record; `validate-flight.py` re-run | 0 | documented; the schedule given in UTC with its New York conversion, never as running |
| Domain sweep | `CONTEXT.md`, `docs/adr/` | — | domain sweep: nothing new |
| Publication | `gh pr create --head intent/new-intent-47c2a273 ...`, then `gh pr view 1 --json state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |

## Discovery

- `orchestration/` holds one Flight, `NycTaxiBuild.Flight` (`config.json` sha256 `acb69b09…0ef5`, `flight.py` `0e35481e…2ce6`, `requirements.txt` `c604fe77…d421`), which builds the whole project under `--target flight` — `ls orchestration/`, `sha256sum orchestration/NycTaxiBuild.Flight/*`
- `agg_driver_daily+` selects `agg_driver_daily`, `agg_driver_monthly` and `mart_driver_scorecard` — `dbt ls --select agg_driver_daily+ --resource-type model --target dev`
- `transformation/profiles.yml` defaults to target `flight` — `grep -n target: transformation/profiles.yml`
- 05:00 `America/New_York` on 2024-01-08 is 10:00 UTC (UTC−5) and on 2024-07-08 09:00 UTC (UTC−4) — `zoneinfo` conversion
