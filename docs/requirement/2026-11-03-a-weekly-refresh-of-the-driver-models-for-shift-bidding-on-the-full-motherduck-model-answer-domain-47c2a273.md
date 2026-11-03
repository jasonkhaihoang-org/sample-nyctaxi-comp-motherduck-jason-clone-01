---
kinds: [orchestration]
---

# Requirement: A weekly refresh of the driver models for shift bidding, on the full MotherDuck model-answer Domain

## Ask

"Shift bidding opens on Monday mornings. Give us a refresh that rebuilds just the driver models — driver day, driver month and the scorecard — every Monday at 05:00 New York time. Don't change the existing NycTaxiBuild Flight." Shift bidding consumes the driver models.

## Requirements

- [ ] `R-01` A new Flight under `orchestration/` refreshes the driver models weekly, beside `NycTaxiBuild.Flight`, which is unchanged — accept when `orchestration/<Name>.Flight/` exists with action `create`, and `NycTaxiBuild.Flight`'s three files keep their checksums — source: request, answer (shape)
- [ ] `R-02` It runs no ingestion and builds `agg_driver_daily` and everything downstream of it — accept when `flight.py` is the plugin's dbt Flight template running `deps` then `build --select agg_driver_daily+` (`agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard`), with no dlt step — source: request, answers (downstream, no reload)
- [ ] `R-03` It is scheduled for Mondays at 05:00 New York time, committed and never activated — accept when `config.json` carries a five-field UTC `schedule_cron` for that time with its conversion and daylight-saving drift recorded, and no Flight is left scheduled — source: request, answers (time zone, cron)
- [ ] `R-04` The Flight passes its validator and one green sandbox run — accept when `validate-flight.py` exits 0 and a run against the Ephemeral database at the Intent branch ends `SUCCEEDED`, exit code 0, with the `dbt succeeded:` line in its own logs — source: plugin `motherduck/orchestration.md`, `flight-sandbox-run.md`
- [ ] `R-05` Nothing is written to or run against `sa_prd` — accept when the sandbox run overrides `DESTINATION_DATABASE` to `VD_EPHM_MOTHERDUCK_DATABASE`, `DBT_SCHEMA` to the Intent's schema and `GIT_REF` to the Intent branch, and no schedule is activated — source: repository (`workarounds` skill), plugin `motherduck/orchestration.md`

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Shape | A separate weekly Flight; `NycTaxiBuild.Flight` keeps its whole-project build unchanged | request; user answer (shape) |
| Invoked workloads | `dbt build --select agg_driver_daily+`: `agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard`; no source reload, since the daily refresh loads the sources | request; user answers (downstream, no reload) |
| Schedule | Mondays 05:00 `America/New_York`, not UTC | request; user answer (time zone) |
| Cron | `0 9 * * 1` (UTC): 05:00 New York during daylight saving (EDT, UTC−4) and 04:00 in winter (EST, UTC−5), so the refresh is never late; a Flight cron is UTC and cannot follow the clock change | user answer (cron, recommended) |
| Activation | Never in the sandbox; a cadence needs a Business plan, and customer CI/CD activates it | plugin `flight-authoring.md` |

## Out of scope

`orchestration/NycTaxiBuild.Flight` and the dlt Flights are unchanged; no dlt Flight is scheduled. No model changes.

## Open questions

None.

## Approvals
- 2026-11-03T20:33:48Z — requirement approved — "Approve and continue to design." — 226aff9
- 2026-11-03T20:34:27Z — design approved — "Approve and continue to planning." — daf31d9
- 2026-11-03T20:40:32Z — ship approved — "approved" — edf6d9d
