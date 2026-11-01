---
name: semantic-model
description: "Use when the Domain's Ossie documents (Apache Ossie with VIBEDATA payloads) must be created, reverse-engineered from boundary dbt models, extended with a star, aggregate source, metric or level, refactored, or brought up to date after a boundary dbt model change, or when asked which source supplies a field or why a table is unmapped. Do not use to review the Ossie documents before commit (use validating-semantic-model) or to author dbt models (use generating-dbt-model)."
user-invocable: false
---

# Semantic Model

Leaves the Domain's Ossie documents, one flat Apache Ossie `0.2.0.dev0` document per file with `VIBEDATA` payloads, each anchored on a star (a fact and the dimensions it reaches), and the dbt tests generated from it, current and green. Consumer formats (Tableau, PowerBI) export from it on the fly and are never committed.

| Term | Means |
| --- | --- |
| **dbt model** | One SQL file plus its entry in a dbt properties YAML |
| **Ossie document** | One `*.ossie.yaml` under `logical-model/`; one star per document |
| **Ossie dataset** | One `datasets[]` entry inside an Ossie document |
| **semantic layer** | The Domain's Ossie documents plus its ontology, as a whole |

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it. Every command runs from the Domain's repository root and prints JSON on stdout, exiting 0 when it finds nothing to fix and 1 otherwise.

## Process

1. Read `CONTEXT.md`, then resolve the four Domain paths below from the Domain's `repo-map.json`, taking the default where the Domain declares none, and use them in every later step.

   | Path | Read from `repo-map.json` | Default |
   | --- | --- | --- |
   | Ossie directory | the directory of `artifact_paths.logical_model` | `logical-model/` |
   | Semantic roots | the `layers.<name>.path` of every layer with role `boundary` (explicit, or derived: `built_by: dlt` → `input`; else named in `gold_layers` → `boundary`; else `internal`), or `artifact_paths.dbt_project` plus `models/marts/` when the Domain declares no layers | `transformation/models/marts/` |
   | Singular tests directory | `artifact_paths.singular_tests` | `transformation/tests/` |
   | Decision-record directory | the directory of `artifact_paths.adr` | `docs/adr/` |

2. Run `python3 "$SKILL_DIR/scripts/ossie.py" version`. When it fails on a missing module, run `python3 -m pip install -r "$SKILL_DIR/scripts/requirements.txt"` once and retry; halt and report the error if it still fails.
3. Read every Ossie document in the Ossie directory and the SQL of every mart the change touches, then read the reference the change needs.

   | The change | Read |
   | --- | --- |
   | Onboarding a lakehouse, a new mart, or a table with no honest mapping, and where a bespoke table goes | `references/reverse-engineering.md` |
   | A split, fold, rename, grain change, business-rule change, aggregate lifecycle or star retirement | `references/refactoring.md` |
   | What a `VIBEDATA` payload field means, or which ratio or average a metric is | `references/vibedata-fields.md` |
   | A new document | `examples/star.ossie.yaml` |

4. Before adding any boundary relation to a document, route it with the table under Routing a bespoke table: a group-level cut (`HAVING` floor), a lossy join or a different method goes to `semantic_exclusions`, not a source.
5. Author the change under the modelling rules S1–S7a in `references/modeling-rules.md`; the quick reference below answers the common questions. Never edit boundary dbt model SQL, a seed or a macro to fit the Ossie documents: they record what the lakehouse does.
6. Regenerate the tests the Ossie documents own with `python3 "$SKILL_DIR/scripts/ossie.py" generate-tests <model-dir> <tests-dir>`, and never edit them by hand. It writes `assert_semantic_content_holds.sql` (every aggregate binding against the detail, group by group), `assert_semantic_level_keys_hold.sql` (level keys that break a join; severity `error`) and `assert_semantic_levels_hold.sql` (every other departure from the declared levels; severity `warn`).
7. Run the structural gates and require exit 0 from the whole chain; fix a failure and re-run before going further. Pass every boundary layer path from the repo map as a `<boundary-layer-root>` and each relation in its `semantic_exclusions` as an `--exclude`.

   ```bash
   SKILL_DIR="<this skill's directory>" && python3 "$SKILL_DIR/scripts/ossie.py" validate <model-dir> && python3 "$SKILL_DIR/scripts/ossie.py" coverage <model-dir> <boundary-layer-root>... [--exclude <relation>]... && python3 "$SKILL_DIR/scripts/ossie.py" suppliers <model-dir> && python3 "$SKILL_DIR/scripts/ossie.py" notes <model-dir> <tests-dir> <adr-dir> && python3 "$SKILL_DIR/scripts/ossie.py" generate-tests <model-dir> <tests-dir> --check
   ```

8. Load `validating-semantic-model` for the content review before commit.
9. When the Domain has an ontology, the ontology changes in the same change: invoke `ontology` for every dataset this change adds, renames, re-grains or re-keys that a concept reaches, and re-run its `refs` gate even when no mapping was edited, because a renamed or re-keyed field breaks a mapping silently.

   When the Domain declares `artifact_paths.data_contract` and the change adds, renames, retypes or re-keys a field of a boundary dataset, update that relation's contract in the same change through `data-contract`; its `check` fails a contract that disagrees with the document.
10. Commit the Ossie documents, the regenerated tests and any ontology or contract change together, in the same change as any mart change that moved them, and record each gate command with its exit code where the current task keeps its evidence.

## Quick reference

| Question | Answer |
| --- | --- |
| Where does a refused column go? | The detail source's `note`, naming each column and why |
| Where does an unmappable table's reason go? | A `note` on its entry when it is mapped; otherwise a `semantic_exclusions` reason in the repo map |
| Where does a blocked decision go? | Ask first (`references/reverse-engineering.md`); write the entry plus its `note` only once ruled |
| Where does a business rule go? | The Domain's decision record (ADR). The Ossie documents cite the rule; they never restate it |
| Where does a bespoke table go? | By what its rows are (below); the SQL documents an excluded table, so no document is written for it |
| Detail or aggregate priority? | Detail-class `1` (one per role), aggregate `0` |
| What does an aggregate declare beyond its `column_map`? | `content_levels` from its `GROUP BY`, `content_filter` from its `WHERE` and inner joins, held by a test its `note` names (S3b) |
| A rate or ratio? | A `derived_expression` over its numerator and denominator metrics, bound to no column (S3c) |
| A level? | Declared once on the dimension (`levels[]`) with `keys[]`: exactly one primary, at most one display, every key unique at the level by declaration; a repeating name is an attribute (S5a) |
| A metric's population (billable only)? | `filter` on the base metric, read by its core expression too (S3c) |
| Grouped by a dimension its fact cannot reach? | Error by default; a separate metric with `unrelated_dimensions: total` repeats the value. Check with `ossie.py dimensionality` (S3c) |
| A bridge that fans a store out to its departments? | A relationship with `to_level` and `weight`; the weights sum to 1, held by a test (S4) |
| A month table beside the day table? | A `priority_group: 0` source of the same dimension with an own-level `content_levels` entry (S3b) |
| Sum per day, then average? Closing headcount? Mean of store averages? | A dimension-based aggregation rule: `based_on_dimensions` across the inner level with the right `rule` (S3c) |
| Can an aggregate answer this query? | `ossie.py compile <model-file> <query-file>` names the source it chose and why it rejected each other one (S7a) |
| Does every mapped column exist, with a compatible type? | After a build and `dbt docs generate`, `ossie.py columns <model-dir> <catalog.json>` |
| Does each aggregate binding match its SQL, and is no source cut by a HAVING floor? | After `dbt compile`, `ossie.py bindings <model-dir> <manifest.json>`; no warehouse needed |

### Routing a bespoke table

| The table is | It becomes |
| --- | --- |
| The star's rows rolled up | An aggregate logical source |
| A narrower population a row filter on the star states (billable, a payment class) | A filtered metric (`filter`) |
| A group-level cut (`HAVING` floor), a row-dropping or lossy join, a different method, stacked slices, a long or wide reshape | Excluded: `semantic_exclusions: [{relation, reason}]` in the repo map |
| A new business process | A new star |

## Common mistakes

- Identity column maps assumed from siblings. Verify every right-side column against the mart definitions.
- A new physical table without its `physical_joins` entries. The table exists but no query can reach it; `table-unjoined` warns.
- A new key invented inline instead of arriving with its schema, validator and test change. `unknown-key` fails it.
- A `content_filter` copied from the mart's `WHERE` alone. Every inner join drops null-key rows too, and the content test fails on the difference.
- Window bounds that differ from the dbt vars that bound the mart. Write the dates the vars hold; the content test fails when the two drift.

## Red flags — stop and re-check

- "Validate is green, so the mapping is semantically right." Green proves shape and references, never business correctness.
- "The aggregate table must carry this column." Read the aggregate's SQL; its grain decides, not hope.
- "I haven't read the boundary dbt model SQL, but the column name is obvious." Stop: no mapping without reading the dbt model definitions. An unreadable dbt model is an unmapped source with a `note` (or an exclusion with its reason), never an assumed map.
- "One more key won't hurt." It fails. Use the schema file.
- "The aggregate obviously covers the same rows." Write the `content_filter` and run the content test; an inner join says otherwise more often than not.
- "The level test reports a repeated key, so I'll weaken the level." The declaration is the intent; record the data finding where it belongs.

All of these mean: read the SQL, state what it does, and let the generated tests hold it.
