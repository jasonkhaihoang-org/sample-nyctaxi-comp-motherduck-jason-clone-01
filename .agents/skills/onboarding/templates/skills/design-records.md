---
name: design-records
description: "Use when writing or amending a design record under docs/design/ for a model or pipeline."
---

# What goes into a design record (E9)
<!-- onboarding
ask: no
reason: A platform content rule or workaround; the same for every domain.
-->

## Scope

- One record per model or pipeline, amended by later changes, never one per change.
- Record only what the code and catalog cannot tell a reader.

## Decisions

- `D-NN`, append-only, each with its source: a requirement, an answer or a convention.
- Where an ADR governs a decision, cite it as `ADR NNNN` with a link. When that ADR is superseded, cite its successor.
- Pipeline records: per resource, the write disposition, incremental cursor, the three schema-contract axes (`columns`, `tables`, `data_type`) and the duplicate-key handling.

## Consumers

- Lists dependents only: the models and pipelines in this repo that depend on this one, taken from lineage (`dbt ls --select <model>+`).
- No teams, reports, packs or audiences.
- When nothing in the repo depends on it, write "None in this repo".

## No evidence

A design record holds decisions, not measurements. Counts, profiling results, reconciliation figures and check outcomes go in the intent's verification file: they change with every load, and a copy in the design record drifts from the data. A decision whose reason is a measurement says so in words and names that verification file.

## Areas

A decision shared by several models is recorded once, in an area design at `docs/design/<area>/<subject>.md` (for example `docs/design/<area>/order-identity.md`, area `orders`), and each model's record cites it. An area is never named `models` or `pipelines`.
