---
kinds: [ingestion, transformation]
---

# Requirement: Pending request R4: onboard the TLC high-volume for-hire feed with a daily zone aggregate, on the full MotherDuck model-answer Domain

## Ask

"Onboard the TLC high-volume for-hire feed as a new source — staging model plus a daily zone-level aggregate, so we can put their volume next to ours." Fleet Operations analytics consumes the aggregate beside the existing daily zone taxi aggregate, `agg_trip_zone_daily`; "ours" is every yellow and green trip as that aggregate counts them.

## Requirements

- [ ] `R-01` The TLC HVFHV trip records for January 2024 land in bronze as one full load, after the pipeline and its docs are final — accept when the loaded row count equals the source file's row count and every pickup falls on 2024-01-01 to 2024-01-31 — source: answers (window, load size)
- [ ] `R-02` A staging model holds one row per bronze HVFHV row, renamed and typed as the existing TLC staging models are — accept when its row count equals bronze and its zone and time columns carry the TLC staging names — source: request
- [ ] `R-03` A new daily aggregate holds one row per pickup zone per pickup date with the HVFHV trip count — accept when its counts sum to the staged rows in the reporting window, unknown zones included, and (zone, date) is unique — source: request, answers (grain, measure)
- [ ] `R-04` The aggregate is keyed like `agg_trip_zone_daily` (`pickup_location_id`, `pickup_date`, same types) so the two sit side by side — accept when both keys carry the same names and types as in that aggregate's contract — source: answer (grain)
- [ ] `R-05` Existing models are unchanged: HVFHV is not merged into the conformed trips or `fct_trip` — accept when no existing model's SQL changes and the rebuilt existing models match the Domain — source: answer (reuse), ADR 0006, proposal 0001 (`proposed`)
- [ ] `R-06` The semantic layer moves with the aggregate — accept when the Ossie and ontology gates exit 0 — source: repository (`workarounds` skill)
- [ ] `R-07` Nothing is written to the Domain database `sa_prd` — accept when every load runs on the `tlc_pipeline` Flight with its database overridden to the Intent's Ephemeral database and `GIT_REF` to the Intent branch, each load's own log names the Ephemeral database, and every dbt build runs on target `dev` — source: repository (`workarounds` skill), plugin `motherduck/dlt.md`, `motherduck/dbt.md`

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Load window | January 2024 only. This differs from ADR 0005's three-month window ("The loaded window is three months"), so February and March show taxi volume with no HVFHV beside it | user answer, after the conflict with ADR 0005 was named |
| Load size | Sample loads while building; one full load once the pipeline and its docs are final | user answer |
| History | Full replace each run | ADR 0005: "reloaded in full on every run (`replace`), with no sampling" |
| Grain of the aggregate | One row per pickup zone per pickup date | user answer (recommended) |
| Measure | HVFHV trip count only; no fares, revenue, driver pay or miles; one combined count, no split by licensee | user answer |
| Population | Every HVFHV trip in the reporting window; no billable rule | ADR 0003: the rule is "applied where revenue and flows are reported"; user answer |
| Unknown zones | Kept, never dropped or remapped | ADR 0012: "The warehouse keeps them … and does not remap or drop them." |
| Reuse | A new aggregate beside `agg_trip_zone_daily`; no merge into `fct_trip` | user answer, ADR 0006, proposal 0001 (`proposed`) |
| Source shape | HVFHV is a resource on the existing `tlc` source, not a new source, although the request says "new source" | `.agents/skills/dlt/SKILL.md`: "Another table from a source that is already loaded (for example another TLC trip file) is a resource on that source, not a new source" |

## Out of scope

The existing TLC resources and their three-month window, the conformed trips, `fct_trip`, `agg_trip_zone_daily` and every published mart. Bringing HVFHV into the conformed trip grain is proposal 0001, still `proposed`.

## Open questions

None.

## Approvals
- 2026-11-03T19:53:35Z — requirement approved — "Approve and continue to design." — c88d4d4
- 2026-11-03T19:54:29Z — design approved — "Approve and continue to planning." — b4df645
- 2026-11-03T20:20:05Z — ship approved — "approved" — 135b458
