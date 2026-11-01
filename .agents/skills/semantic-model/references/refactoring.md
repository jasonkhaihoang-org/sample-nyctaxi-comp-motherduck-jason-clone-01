# Refactoring the Ossie documents

Use when the Ossie documents' structure or a definition changes: splitting, folding, renaming, a grain change, a business-rule change, an aggregate's lifecycle, or a star's retirement. Everyday edits do not need this file.

The Ossie documents are not append-only. These moves are normal work, each validated across every file afterwards, with no dual sources of truth left behind:

- **Fold an excluded table into a star.** When a join key lands, remove its `semantic_exclusions` entry, add the dataset to the consuming document with the relationship and its `physical_joins` entry, and correct every stale statement about the table wherever it lives — its `note`, description, `ai_context`, and any rule the new path invalidates. A table is mapped once; relationships cannot cross documents.
- **Split the Ossie documents.** Partition by whole stars, as the atomic-stars rule (S1 in `./modeling-rules.md`) requires; each document keeps every dataset its own facts need, and shared dims are copied so their identity matches.
- **Move or rename a dataset.** Update every relationship, `physical_join`, and `logical_sources[].physical_table` that names it in the same change; leave no dangling reference for validation to find.
- **Rename a field, metric or relationship.** Content and metric payloads name them too: `content_filter`, `content_levels[].via`/`key_columns`, level `keys[].fields` and `attributes`, `row_level`, `derived_expression`, `at_levels`, `time_series.of`/`via`, `based_on_dimensions.of`/`across`. After any level, key or content change, regenerate the tests with `ossie.py generate-tests`. `validate` fails each one left behind.

Name new relationships and joins after the existing pattern in the target document; when you are creating the document there is no pattern yet, so follow `../examples/star.ossie.yaml` (`<fact>_to_<target>`, `fct_<fact>_to_<table>`, `LTS<n>_<purpose>`).

### Aggregate source or exclusion

The routing table in `../SKILL.md` gives the dispositions. Population decides: a source whose rows are the star's population rolled up is an aggregate even when its SQL filters or windows them, while a table that answers a different question would make a metric lie if mapped, so it is excluded. A consumption mart whose grain matches its fact and whose sum columns are additive is an aggregate source (its ranks and ratios stay unmapped, refused in notes); one whose grain crosses the fact's is excluded.

### Fact-grain change

When a fact's grain changes, the primary key, the detail `content_grain`, every aggregate's `content_levels`, and every count metric change together: a `SUM(CASE ...)`-style count silently becomes a finer-grained count, so count metrics need the distinct rollup key while additive money metrics stay sums. Then establish — by reading each aggregate's SQL, never by assumption — whether that aggregate was rebuilt at the old grain or the new one; if the answer is not available, that is a blocked-mapping question (`./reverse-engineering.md`), not a default. A metric whose grain disagrees with the aggregate source supplying it is the most expensive silent error in the Ossie documents.

### Business-rule change

When a definition changes (billable, active, in-window), the `content_filter` of every source that applies it changes in the same edit, and so does the holding test; a filter that still states the old rule lets an engine route a query to a source that no longer holds those rows. Also withdraw — do not merely annotate — every binding whose source computes the old rule; a note alone leaves the stale column bindable, and a priority-0 aggregate outranks the already-correct detail. Withdraw the whole dependency chain: a field whose only supplier is withdrawn cannot stay declared, and a metric whose expression names a withdrawn field is a lie, so the field and metric go with the mapping. One source-level `note` covers a partial withdrawal: name every withdrawn binding and its exact restore condition in it. Correct any `ai_context` that states the old rule, move the rule itself into the Domain's decision record, and record the restore as one tracked follow-up per change (decision-record revision or issue), never as memory. An empty `column_map` is a tombstone and must carry that note.

### Aggregate lifecycle

- **Added**: register the table, its join, and its source at honest grain, with `content_levels` and `content_filter` written from its SQL and its bound totals added to the holding test.
- **Rebuilt at a different grain**: re-derive that source's `content_grain`, `content_levels` and `column_map` as a grain change.
- **Filter or join changed**: a new `WHERE` clause, or a left join turned inner, changes the rows the source holds; re-derive its `content_filter` and re-run the holding test.
- **Absorbed by detail** (detail now answers everything the aggregate did): drop the mappings and the handle once nothing names it; a dead aggregate is a stale definition waiting to be trusted.
- **Retired**: delete the handle, its joins, and every source naming it in the same change.

### Star decommission

Deleting a fact star means deleting its document and the handles only it used, after moving the decisions and reasons it carried into the Domain's decision record. A document left behind holding half a star is worse than no document: it still validates.

Business rules live in the Domain's decision record, not in the Ossie documents: a threshold, filter or bound that changes the answer is an ADR, and the Ossie documents cite it. When a refactor makes a stated rule wrong on one path, that is a business ruling — ask under the blocked-mapping rule in `./reverse-engineering.md`; never quietly rewrite the rule to fit the new shape.
