---
artifacts: [DriverWeeklyRefresh]
---

# DriverWeeklyRefresh

The weekly refresh of the driver models for shift bidding: a dbt Flight at `orchestration/DriverWeeklyRefresh.Flight/`, beside `NycTaxiBuild.Flight`.

## Decisions

- `D-01` A separate Flight, action `create`, so the weekly cadence has its own schedule and fails on its own; `NycTaxiBuild.Flight` keeps its whole-project build unchanged. [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md) governs the dlt pipelines that load the sources, not a dbt-only refresh, so it does not shape this Flight. Source: docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md R-01, request, user answer (shape).
- `D-02` `flight.py` is the plugin's dbt Flight template: it checks out the Domain repository at `GIT_REF` and runs `dbt deps`, then `dbt build --select agg_driver_daily+` (`agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard`) under the profile's default `flight` target. No dlt step: the daily refresh loads the sources. Source: docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md R-02, user answers (downstream, no reload), plugin `motherduck/templates/flight-dbt.py`.
- `D-03` `schedule_cron` is `0 9 * * 1` (UTC): Mondays at 05:00 New York during daylight saving (EDT, UTC−4: 05:00 + 4 h = 09:00 UTC) and at 04:00 in winter (EST, UTC−5: 09:00 − 5 h = 04:00). A Flight cron is UTC and cannot follow the clock change, so the run is an hour early from November to March rather than an hour late from March to November. Source: docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md R-03, user answers (time zone, cron).
- `D-04` `config.json` declares every key `flight.py` reads with its production value — `GIT_REF` `main`, `DESTINATION_DATABASE` `sa_prd`, `DBT_SCHEMA` `main`, `DBT_EMPTY_RUN` `false` — plus `schedule_cron` and the git secret in `flight_secret_names`; `requirements.txt` is `NycTaxiBuild.Flight`'s, every dependency pinned with `==`. Source: docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md R-04, plugin `motherduck/flight-authoring.md` (config.json is the declared key set).
- `D-05` The schedule is never activated by the agent: a sandbox apply holds `schedule_cron` back, and customer CI/CD deploys it (a cadence needs a MotherDuck Business plan). Source: docs/requirement/2026-11-03-a-weekly-refresh-of-the-driver-models-for-shift-bidding-on-the-full-motherduck-model-answer-domain-47c2a273.md R-03, R-05, plugin `motherduck/flight-authoring.md`.

## Rejected

- Adding a weekly mode to `NycTaxiBuild.Flight`: the request keeps it unchanged.
- `0 10 * * 1`: 05:00 in winter but 06:00 during daylight saving, an hour after bidding could open.
- Scheduling the dlt Flights: no source reload is needed, and the plugin reports scheduling an ingestion Flight as a gap.

## Consumers

None in this repo.

## History

- 2026-11-03 — new-intent-47c2a273 — design record written for a new weekly dbt Flight; terms: none new — D-01 to D-05
