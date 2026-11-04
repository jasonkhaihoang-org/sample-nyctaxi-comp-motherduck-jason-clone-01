# Verification: Migrate, not add: one zone-day roll-up shared by mart_daily_zone_revenue and agg_trip_zone_daily, nothing a consumer reads changed, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `3202b9c`: `agg_trip_zone_daily_base` computes the zone-day roll-up once, and `mart_daily_zone_revenue` and `agg_trip_zone_daily` build on it with no read of `fct_trip` of their own. Both rebuilt relations in the Intent's Ephemeral MotherDuck database (`vd_eval_20261104072731_aab43ba9f5c0_eph`) equal the Domain's released ones in name, columns, column order, types and rows: `mart_daily_zone_revenue` 11 columns and 20,770 rows, `agg_trip_zone_daily` 14 columns and 20,771 rows. The semantic layer passes every gate with only a registration note added. Nothing was written to `sa_prd`.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` one shared roll-up | `git diff 7fcde94 3202b9c -- transformation/models`: neither model refs `fct_trip`; both ref `agg_trip_zone_daily_base` | pass | `3202b9c` |
| `R-02` `mart_daily_zone_revenue` unchanged | Refactor equivalence (below) against `sa_prd`'s `finance.mart_daily_zone_revenue` | 11 of 11 columns in order and type; 20,770 rows; every column's non-null count and value hash equal | `3202b9c` |
| `R-03` `agg_trip_zone_daily` unchanged | Refactor equivalence against `agg.agg_trip_zone_daily` | 14 of 14 columns in order and type; 20,771 rows; every column equal | `3202b9c` |
| `R-04` billable rule in gold, distinct drivers | unit test `trip_zone_daily_base_keeps_both_populations`; `R-02`, `R-03` | PASS; one driver with a billable and a non-billable trip counts once | `3202b9c` |
| `R-05` semantic layer | Gate results below | exit 0 each; no dataset, metric or logical source changed | `3202b9c` |
| `R-06` nothing in `sa_prd` | each gate's `run_results.json`; every command on `--target dev` | all three relations in `vd_eval_20261104072731_aab43ba9f5c0_eph` = `VD_EPHM_MOTHERDUCK_DATABASE`; no Flight run | `3202b9c` |

## Refactor equivalence

One comparison per relation over pinned identical inputs: the Ephemeral database is a clone of `sa_prd` and every upstream model is deferred to it, so both sides read the same `fct_trip` and `dim_zone`. For each relation, read once from `vd_eval_20261104072731_aab43ba9f5c0_eph` and once from `sa_prd`: the column list in order, `typeof()` of each column, `count(*)`, and per column `count(col)` and `sum(hash(col))`, a DOUBLE hashed as `round(col, 2)`. Frozen tolerance: a DOUBLE at the cent (its values are sums of cent amounts whose last bits move with aggregation order), every other type exact.

| Relation | Columns | Types | Rows | Per-column counts and hashes |
| --- | --- | --- | --- | --- |
| `mart_daily_zone_revenue` | 11, same order | same | 20,770 = 20,770 | 11 of 11 equal |
| `agg_trip_zone_daily` | 14, same order | same | 20,771 = 20,771 | 14 of 14 equal |

Control: the mart built once over every trip (no billable filter) gave 20,771 rows against 20,770, and the comparison failed it.

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Model gates | `dbt build --select "<model> state:modified+,+<model>" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`, for `mart_daily_zone_revenue` and `agg_trip_zone_daily` | 0, 0 | pass: PASS=18 WARN=1 each (the existing `assert_semantic_levels_hold` finding); both unit tests PASS |
| Project audit | `dbt build --select package:dbt_project_evaluator --vars '{dbt_project_evaluator_enabled: true}' --warn-error-options '{"error":["NoNodesForSelectionCriteria"]}' --target dev` | 0 | pass: PASS=66 WARN=12 ERROR=0 |
| Ossie chain | `ossie.py validate`, `coverage logical-model transformation/models/marts`, `suppliers`, `notes`, `generate-tests --check`; `tools/ossie_lint.py` | 0 each | pass |
| Repository tests and lint | `python3 -m pytest tests -q`; `ruff check .` | 0, 0 | pass: 203 passed at `01363f6`, after ADR 0003 was made to list the new design record (`test_every_cited_adr_lists_the_record` found it missing); all checks passed |
| Baseline cross-check | `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | 0 | pass: exactly `agg_trip_zone_daily_base`, `agg_trip_zone_daily`, `mart_daily_zone_revenue` = the Plan's three; `manifest-source.json` `build_sha` `7fcde94` |
| Logical Model contract | each record's `## Logical Model` against the document | — | pass: nothing added, changed or retired; the registration note present |
| Docs match data | the three records and the `_agg.yml` entry against the built relations | — | pass |
| Dev-artifact scan | `git diff 7fcde94 3202b9c` | — | pass: no dev_mode, limit, environment id or profile edit |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | pass: fresh |
| Contract promotion | no enforced contract on the three models | — | not applicable |
| Domain sweep | `CONTEXT.md`, `docs/adr/` | — | domain sweep: nothing new |
| Publication | `gh pr create --head intent/new-intent-3e385ecb --base main ...`, then `gh pr view 1 --json state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |
