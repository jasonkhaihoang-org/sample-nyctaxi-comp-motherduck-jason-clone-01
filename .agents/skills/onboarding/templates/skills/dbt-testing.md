---
name: dbt-testing
description: "Use when writing, changing or running dbt tests, unit tests or Python tests, or when comparing rebuilt values."
---

# dbt testing
<!-- onboarding
ask: no
reason: Index text; sections below carry the decisions.
-->

## Generic tests (C1)
<!-- onboarding
ask: yes
question: Which generic tests are required?
recommended: `unique` and `not_null` on every primary key, `relationships` to conformed dimensions, `accepted_values` on closed sets.
alternatives: only the tests a requirement names.
-->

- Every primary key has `unique` and `not_null`.
- Every foreign key to a conformed dimension has `relationships`.
- A column with a closed set of values has `accepted_values`.
- Arguments go under `arguments:`.

## Freshness (C2)
<!-- onboarding
ask: yes
question: Which sources declare freshness?
recommended: Sources loaded on a schedule; one-off loads none.
alternatives: every source.
-->

Declare source freshness where a source is loaded on a schedule. A source loaded as a one-off needs none.

## Singular tests (C4)
<!-- onboarding
ask: yes
question: Where do singular tests live and how are they named?
recommended: `transformation/tests/assert_<what_must_hold>.sql`, returning violating rows.
alternatives: one folder per layer.
-->

Live in `transformation/tests/`, named `assert_<what_must_hold>.sql`, and return the rows that violate the assertion.

## Rejoin tests (C10)
<!-- onboarding
ask: no
reason: A key mismatch builds green; learned from a real defect.
-->

A left join on a derived key (a hashed or concatenated key built in two places) gets a singular test that every row on the left finds its match, or that the unmatched rows are the ones expected. A left join reports a miss as a null, so a key mismatch builds green.

## Comparing values
<!-- onboarding
ask: no
reason: A DuckDB property; an exact comparison of rebuilt measures never settles.
-->

DuckDB float aggregation is not reproducible bit for bit: two builds of the same model from the same inputs can differ in the last bits of a `double`. Compare money at the cent (`round(x, 2)`) and other measures with an explicit tolerance, never by hashing raw values. A column the change does not touch counts as unchanged when every row agrees at that precision. A requirement's acceptance condition that compares values names this precision ("equal at the cent", "within 1e-6"), so verification does not read "equal" as bit-for-bit.

## Unit tests (C5)
<!-- onboarding
ask: yes
question: When does a model need a unit test?
recommended: When a branch could be wrong: ordering and tie-breaks, deduplication, state classification.
alternatives: every intermediate model.
-->

A model needs a unit test when its logic has a branch a reviewer could get wrong: ordering and tie-breaks, deduplication, and state classification. Unit tests live in `_unit_tests.yml` beside the dbt model.

Run data tests and unit tests as separate commands. The command for each layer is in `test-map.json`.

A unit test whose model reads a project var sets the var in the test itself, under `overrides: {vars: {<name>: <value>}}`; the project's value does not apply.

## Python tests
<!-- onboarding
ask: no
reason: Map tests and pipeline tests run offline under pytest.
-->

pytest tests live in `tests/`, run offline, and are mapped in `test-map.json`.
