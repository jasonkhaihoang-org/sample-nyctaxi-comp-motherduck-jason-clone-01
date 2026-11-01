# Convention inventory

One row per convention the repo follows. Build it from the code and documents before asking anything.

Record whether `logical-model/` exists. A repo with gold marts and no Ossie document is a review finding, and writing the Ossie documents is part of Build once the marts are stable enough to describe.

| Column | Content |
| --- | --- |
| ID | `C-n` |
| Convention | One sentence, as a rule would state it |
| Evidence | Paths, and a count where it matters: "41 of 44 staging models are `stg_<source>__<table>`" |
| Consistent | `yes`, or the exceptions by name |
| Destination | `repo-map`, `convention skill: <name>`, `domain skill: <name>`, `ADR`, `CONTEXT`, `design record: <model>`, `review` |
| Status | `inferred`, `confirmed`, `changed by user`, `dropped` |

## Where to look

- dbt: `dbt_project.yml` (paths, `+schema`, `+materialized`, vars), model folders and names, properties files, `packages.yml`, macros, singular and unit tests, seeds, `profiles.yml` targets.
- dlt: pipelines, sources, `.dlt/config.toml`, write dispositions, schema contracts, naming, incremental cursors.
- SQL style: `.sqlfluff`, and what the models actually do where the two differ.
- Orchestration and CI: run scripts, Makefile, CI jobs.
- Documents: README, CONTRIBUTING, runbooks, agent instruction files, existing ADRs or design notes, model YAML descriptions.

## Rules hiding in code

Read the models, macros, seeds and pipeline config for **numbers and predicates that change what a result means**, not only for naming and structure:

- numeric thresholds and caps: `having count(*) >= 25`, `max_plausible_mph`, a row limit, a fee percentage, a band boundary;
- predicates that change a population: `where is_billable`, a report window, `is_current_version`, an inner join that drops unmatched rows;
- a `--` comment that explains **why** a rule exists rather than what the code does. That comment is often the only surviving record of a decision that was made in a conversation.

Inventory each one, then apply the destination test: a standing business answer — a threshold, a population definition, a measure definition, a grain — is an `ADR`, which the Domain's `adr` convention skill (from [`templates/skills/adr.md`](../templates/skills/adr.md)) already says qualifies. A rule still undecided, or one whose only rationale is the code itself, is a `review` finding.

A hard-coded number whose reason lives only in a comment is the classic miss. It governs what every consumer sees, no document states it, and the next model binds to it as though it were a law of nature. The origin-destination matrix's 25-trip floor sat that way: `having count(*) >= 25` with a two-line comment, no ADR, until an intent had to write one.

## Destination test

Ask in this order and stop at the first yes:

1. Can a script check it against the file tree? `repo-map`.
2. Is it something that should change? `review`.
3. Does it hold for every change of a kind? `convention skill`.
4. Is it an ordered procedure only this repo has? `domain skill`, after confirmation.
5. Does it record a choice someone made for a reason? `ADR`.
6. Is it a business term? `CONTEXT`.
7. Does it belong to one model or pipeline only? `design record`.

A convention a plugin skill already states is not a convention skill. Drop it.
