---
name: dbt-testing
description: "Use when writing, changing or running dbt tests, unit tests or Python tests, or when comparing rebuilt values."
---

# dbt testing

## Generic tests (C1)

- Every primary key has `unique` and `not_null`. A grain of several columns has `not_null` on each of them and a singular test that it is unique (`assert_<model>_one_row_per_<grain>`). No test uses a `dbt_utils` macro: `packages.yml` does not declare `dbt_utils`, which is installed only as `dbt_project_evaluator`'s dependency.
- Every foreign key to a conformed dimension has `relationships`.
- A column with a closed set of values has `accepted_values`.

## Freshness (C2)

Declare source freshness where a source is loaded on a schedule. A source loaded as a one-off needs none.

## Singular tests (C4)

Live in `transformation/tests/`, named `assert_<what_must_hold>.sql`, and return the rows that violate the assertion.

## Rejoin tests (C10)

A left join on a derived key (a hashed or concatenated key built in two places) gets a singular test that every row on the left finds its match, or that the unmatched rows are the ones expected. Example: `assert_enrichment_rejoin_matches_every_trip.sql`. A left join reports a miss as a null, so a key mismatch builds green.

## Comparing values

DuckDB float aggregation is not reproducible bit for bit: two builds of the same model from the same inputs can differ in the last bits of a `double`. Compare money at the cent (`round(x, 2)`) and other measures with an explicit tolerance, never by hashing raw values. A column the change does not touch counts as unchanged when every row agrees at that precision. A requirement's acceptance condition that compares values names this precision ("equal at the cent", "within 1e-6"), so verification does not read "equal" as bit-for-bit.

## Unit tests (C5)

A model needs a unit test when its logic has a branch a reviewer could get wrong: ordering and tie-breaks, deduplication, and state classification. Today: `int_status_intervals`, `int_trips_enriched`, `int_trips_conformed`, and the rankings in `mart_driver_scorecard` and `agg_trip_zone_daily`. Unit tests live in `_unit_tests.yml` beside the model.

Run data tests and unit tests as separate commands. The command for each layer is in `test-map.json`.

A unit test whose model reads a project var sets the var in the test itself, under `overrides: {vars: {<name>: <value>}}`; the project's value does not apply.

## Python tests

pytest tests live in `tests/`, run offline, and are mapped in `test-map.json`.
