# VIBEDATA fields reference

Every `custom_extensions` entry with `vendor_name: VIBEDATA` carries a JSON-encoded object of one of four shapes, chosen by the Ossie document component it sits on: the semantic model, a dataset, a relationship or a metric. Fields carry none; they are referenced by name from the dataset and metric payloads. ("Document component" is Ossie's own term; "level" in this file means a dimension level only.) Machine shapes live in `../scripts/vibedata-schema.json`; this file explains what each field means. Key set is frozen (S6): unknown keys fail validation.

## Semantic model component

| Field | Meaning | Example |
| --- | --- | --- |
| `vibedata_version` | Payload generation. Currently `"1.6"`: the frozen key set in this file; a document wholly on `"1.5"` is still accepted. Every payload in a document, metric payloads included, carries the same version; bump only when the key set changes, and migrate all payloads together — mixed versions fail validation. History is under *Upgrades* below | `"1.6"` |
| `physical_tables[]` | Full physical inventory: originals plus aliases. One entry per physical table or role | — |
| `physical_tables[].name` | Repo-local handle other blocks reference | `"ShipTo_Customer"` |
| `physical_tables[].source` | `schema.table` (dbt mart) the handle points at | `"core.dim_customer"` |
| `physical_tables[].dbt_model` | dbt `ref()` name that builds this table; aliases name their base dbt model. Links mart changes to the canonical entries they touch | `"dim_customer"` |
| `physical_tables[].table_type` | `TABLE`, `VIEW`, `ALIAS`, `OPAQUE_VIEW`, `STORED_PROC`, or `SYNONYM` | `"ALIAS"` |
| `physical_tables[].alias_of` | Base table handle, ALIAS only | `"dim_customer"` |
| `physical_tables[].partitioned_by[]` | Storage partition columns of this table, only when it is truly partitioned. Partitioning is a property of a physical table, not of the logical dataset | `["order_date"]` |
| `physical_tables[].role` | Business role of the alias, ALIAS only | `"ship-to customer"` |
| `physical_tables[].note` | Why-not or partial-mapping rationale, recorded where it cannot drift | `"truncated at HAVING count>=25; no honest mapping"` |
| `physical_joins[]` | Physical execution joins between handles (one logical join maps to N of these, one per LTS combination) | — |
| `physical_joins[].{name,from,to}` | Join handle and its two physical-table endpoints | — |

## Dataset component

| Field | Meaning | Example |
| --- | --- | --- |
| `scd` | Slowly-changing-dimension shape: `type` (1/2/3), `natural_key`, `valid_from`, `valid_to`, `is_current` (field names), `open_ended_value` (e.g. `"2099-12-31"`) | — |
| `logical_sources[]` | LTS list: every physical path that can supply this logical table (S3) | — |
| `logical_sources[].name` | LTS handle (`LTS1_detail`, `LTS2_daily`) | — |
| `logical_sources[].physical_table` | Handle into the document's `physical_tables` | `"fct_order"` |
| `logical_sources[].priority_group` | `1` on the single detail source, `0` on every aggregate source. Preference among aggregates is not expressible here — the validator reads any non-zero as a detail supplier | `0` |
| `logical_sources[].content_grain` | Grain in the LTS table's own columns where they exist — they may be columns the dataset does not declare — else the logical grain name (`order`). Human-readable, not validated | `["order_date", "store_id"]` |
| `logical_sources[].content_levels[]` | What the source holds, per dimension role (OBIEE LTS *Content*): `{via, level, key, key_columns}`. `via` is a relationship from this dataset and names the role; `level` is a level of the dataset it reaches, or omitted for that dataset's own rows; `key` picks one of the level's keys (default its primary); `key_columns` are this source's columns that carry that key, in key-field order, so the source can be joined to the dimension at that level. A role not listed is aggregated away. The detail source declares none. An engine may answer a query from the source when every level the query groups by is at or above the declared one, and `validate` requires a physical join from the source to the table the relationship reaches, or to a coarser source of that dimension held at the same level (a month table). On a dimension's own coarser source (see *Dimensions held at several grains*), the entry has no `via` and names one of the dataset's own levels | `{"via": "orders_to_date", "level": "month", "key_columns": ["order_month"]}` |
| `logical_sources[].content_filter` | Row predicate every row of the source satisfies, in the dataset's declared fields, values written as literals (OBIEE fragmentation content). Covers the boundary dbt model's `WHERE` **and** the rows its inner joins drop. An engine uses the source only when the query's own filter implies this one. Unlike the removed `where`, it is code, not prose: the validator resolves every name, rejects a `:placeholder` (variables are not supported yet), and a source that binds anything must name the test that holds it (`held by <test>`) in its `note` | `"order_date >= DATE '2024-01-01' AND order_date < DATE '2024-04-01' AND is_billable"` |
| `logical_sources[].navigable` | `false` when the source's population is narrower than any row predicate can state (an engine then reads it only when asked for it by name). A table cut by a `HAVING` floor is excluded, not mapped with this. Default `true` | `false` |
| `logical_sources[].note` | Partial-mapping rationale: which columns were refused and why | `"billable_revenue refused: agg sums unfiltered totals"` |
| `logical_sources[].column_map` | Logical field-or-metric → physical column, per LTS. Aggregates map only what their grain supports; every field needs ≥1 non-`0` supplier | `{"order_date": "order_date"}` |
| `levels[]` | The dimension's levels (OBIEE logical levels), each declared once and shared by every hierarchy that uses it: `name`, `keys[]` and `attributes[]` | `{"name": "month", "keys": [...], "attributes": ["month_name"]}` |
| `levels[].keys[]` | `{name, fields, primary, display}`. Every key identifies one member of its level: unique at that level **by declaration**, whatever the data does. Exactly one key is `primary`: it is what aggregate navigation, joins at the level and blending use. At most one is `display`, the key shown for a member (default: the primary). A month's keys are `month_start_date` (primary) and `[calendar_year, calendar_month]`, never `calendar_month` alone, which repeats every year | `{"name": "year_month", "fields": ["calendar_year", "calendar_month"]}` |
| `levels[].attributes[]` | Descriptive fields of a member that identify nothing, such as a name several members share (`store_name`). Shown and filtered on, never grouped on as if it were the level | `["store_name"]` |
| `row_level` | Which level one row of the dataset is: `{level, versioned}`. `versioned: false` means a row is a member, and the dataset's `primary_key` must be one of that level's keys (`date_key` and `calendar_date` both key a day). `versioned: true` means rows are versions of members: the dataset is Type 2 and its `scd.natural_key` is the level's primary key (a store is `store_natural_key`; `store_key` is a version) | `{"level": "store", "versioned": true}` |
| `hierarchies[]` | Drill paths: `name`, `levels` (level names, coarsest first; each step declares that a member rolls up to exactly one parent), `is_time` (levels order chronologically by their primary keys, which time-series metrics and `FIRST`/`LAST` rules need) and, on a Type 2 dimension only, `scd_rollup`: `as_of` (a member rolls up to the parent it had on the fact's date) or `current` | `{"name": "Geography", "scd_rollup": "as_of", "levels": ["region", "district", "store"]}` |
| `conformed_from` | Optional string. Set on a dimension copied from another star's document: the `name` of the Ossie document that owns it. `validate` fails the copy when that document has no such dataset, when the owner itself carries `conformed_from`, or when the copy differs from the owner (description included) | `"retail_sales"` |

What the data does with these declarations is tested, never obeyed: `ossie.py generate-tests` writes two dbt tests into the Domain's singular tests directory. `assert_semantic_level_keys_hold.sql` (severity `error`) fails on what breaks a join at a level: a row-level primary key that repeats (on a Type 2 dimension, among its current versions) and a key that names several members. `assert_semantic_levels_hold.sql` (severity `warn`) lists every member with several values of a key, member with several parents, and aggregate key value that is no member. The tools that consume the Ossie documents handle such rows (`row_number() = 1` and the like); the declaration stays the intent.

## Relationship component

| Field | Meaning | Example |
| --- | --- | --- |
| `physical_join` | Handle into the document's `physical_joins` — the execution join for this logical relationship | `"fct_order_to_ShipTo_Customer"` |
| `cardinality` | `many-to-one`, `one-to-one`, or `many-to-many` (warns: no core FK equivalent, resolve through a bridge) | `"many-to-one"` |
| `join_type` | SQL join type (`LEFT OUTER`, …) | `"LEFT OUTER"` |
| `join_cost` | Relative cost for LTS selection, lower wins. Comparable only within one Ossie document; the only way to order aggregates, which `priority_group` cannot express | — |
| `note` | Why this relationship is declared without key-covering `to_columns`, or why a reachable path has no relationship | — |
| `join_expression` | Only when the join is **not** the core `from_columns`/`to_columns` equi-join (a range or as-of predicate on a natural key). Written in Ossie's FieldExpr grammar: every column is `<from or to dataset>.<declared field>`, parsed by the shared expression layer, each name resolved, no `:variables`, and not allowed on a dataset-to-itself relationship. The compiler joins on it when present. A fact that stores the as-of resolved surrogate (`selling_store_key`) needs none: the core columns are the executable truth and `scd_rollup: as_of` states the semantics | `"sales.store_id = store.store_natural_key AND sales.sale_date >= store.valid_from_date AND sales.sale_date < store.valid_to_date"` |
| `to_level` | The join reaches a **member** of a level of the target, not one of its rows: `to_columns` must be that level's primary key (`to-level-key-mismatch`). Used when the target is versioned and the source relates to the member across all versions, such as a bridge keyed on the store's natural key. Ossie core then warns `to-column-not-a-key`, which is expected | `"store"` |
| `weight` | A weighted bridge (OBIEE bridge table with a weight column): a numeric field of the `from` dataset. A measure that reaches the `from` dataset through this relationship from its one side (store → its departments) is multiplied by the weight on each row, so the parts sum back to the whole. The weights of one member must sum to 1, held by a test. Without a weight, that one-to-many direction is a fan-out and no measure may cross it | `"allocation_factor"` |

## Metric component

The core `expression` stays the metric's aggregate over detail rows. The payload says how an engine may answer it from anything else.

| Field | Meaning | Example |
| --- | --- | --- |
| `aggregation` | How a pre-aggregated column rolls up to a coarser grain (OBIEE aggregation rule): `SUM`, `MIN`, `MAX`, or `NON_ADDITIVE`, which never rolls up, so only a source at the query's own grain or the detail can answer (distinct counts) | `"SUM"` |
| `derived_expression` | Post-aggregation formula over other metrics (OBIEE logical-column measure). The metric binds to no column: an engine evaluates its inputs at the query's grain, then applies the formula, which is how a rate is rebuilt from summed numerator and denominator. Binding one to a column fails `computed-metric-mapped`; `suppliers` counts it supplied when its inputs are | `"busy_hours * 1.0 / NULLIF(clocked_hours, 0)"` |
| `at_levels[]` | Level-based metric (OBIEE level-based measure): evaluated at these `{via, level}` levels whatever finer level the query groups by. The denominator of a share of parent | `{"via": "sales_to_selling_store", "level": "district"}` |
| `time_series` | OBIEE time-series function: `function` (`AGO` with an `offset` of periods back, `TODATE`, or `ROLLING` with `periods`, the current member and `periods - 1` before it, OBIEE `PERIODROLLING`; the window counts members of the time dimension, so a day with no rows still takes its place in it), `of` (the metric shifted, whose core `expression` this metric must repeat), and the period as `via`/`level`, a level in a time hierarchy (`is_time`) whose primary key is the chronological key | `{"function": "AGO", "of": "billable_revenue", "via": "orders_to_date", "level": "month", "offset": 1}` |

| `based_on_dimensions` | OBIEE dimension-based aggregation rule: `of` is evaluated at the query's grain refined by the `across` levels, then `rule` (`AVG`, `SUM`, `MIN`, `MAX`, `MEDIAN`, `FIRST`, `LAST`) aggregates those values across that dimension, while every other dimension keeps `of`'s own aggregation. "Average daily revenue" is revenue, `AVG` across Time at day. Only members that have rows take part. `FIRST` and `LAST` take exactly one level, in a time hierarchy: an opening or closing value. The core `expression` repeats `of`'s, and the metric binds to no column | `{"of": "billable_revenue", "across": [{"via": "orders_to_date", "level": "day"}], "rule": "AVG"}` |

| `filter` | OBIEE `FILTER(measure USING ...)`: the rows the metric reads, as a predicate over `dataset.field` columns. The core `expression` must read every column the filter names (`filter-not-in-expression`), so the declared and the computed population cannot part. Only a base or level-based metric declares one; a computed metric inherits its inputs' filters | `"orders.is_billable"` |
| `unrelated_dimensions` | What a query gets when it groups or filters the metric by a dimension its fact cannot reach (see *Dimensions a metric cannot reach*): `error` (default) rejects the query; `total` evaluates the metric without that dimension and repeats the value | `"total"` |

A metric declares at most one of `derived_expression`, `at_levels`, `time_series` and `based_on_dimensions` (`metric-semantics-conflict`); compose them as a chain of metrics instead, and the chain may not loop (`metric-cycle`). `at_levels`, `time_series` and `based_on_dimensions` change what the number means but not the core `expression`, so a consumer that ignores VIBEDATA must not expose those metrics: its value would be the base metric's.

### Evaluation order

OBIEE separates measures computed from rows (physical-column measures, aggregated by their aggregation rule) from logical-column calculations, applied after aggregation. An engine evaluates a metric for one query context (a grain plus filters) in that order, and evaluates every context afresh, totals included:

1. A base metric aggregates rows (the detail, or an aggregate source whose content covers the context) at the context's grain, and rolls up by its `aggregation`.
2. `at_levels` replaces the context's grain on the named roles with the pinned level (a level-based measure). `time_series` replaces its period (`AGO`, `TODATE`). `based_on_dimensions` refines its grain by the `across` levels and then applies its rule across them (a dimension-based aggregation rule). Each applies to the metric it names, so a chain applies from the outside in: the prior month of a closing value shifts the period first, then takes the closing day inside it.
3. `derived_expression` is applied last, to inputs already evaluated in the current context (a logical-column calculation). A time-series or dimension-rule metric over a rate therefore shifts or aggregates the **inputs** and re-applies the formula. Month-to-date utilisation is to-date busy hours over to-date clocked hours, never a running sum of daily rates; an employee's rate inside `mean_employee_utilisation_rate` is rebuilt from that employee's sums.

A total equals the sum of the rows above it only when every link in the metric's chain is a `SUM`. For every other chain, the total is evaluated at the total's own grain. (Cross-check: this matches Essbase two-pass calculation and MDX non-visual totals.)

### Choosing a source for a filtered metric

A source with a `content_filter` holds only some rows. It may answer metric M for query Q when Q's filter **and** M's `filter` together imply the source's `content_filter`. `mart_daily_store_revenue` holds billable orders only, so it can answer `billable_revenue` (whose filter is `orders.is_billable`) for any in-window query, but `order_count` only for a query that itself filters to billable orders.

### Dimensions a metric cannot reach

A metric reaches a dimension through many-to-one relationships from its fact, and through a weighted bridge entered from its one side. `ossie.py dimensionality <model-dir>` prints, per metric, its facts and the dimensions it reaches; a derived metric reaches what all its inputs reach, and a `total` input reaches everything. When a query groups or filters a metric by a dimension outside that set (a single-fact query with no path, or a multi-fact query that brings the dimension in through another fact), the engine decides while planning, before any SQL runs:

- `error`: the whole query is rejected, naming the metric, the dimension and the role. No partial result is returned (OBIEE nQSError 14025).
- `total`: the metric is evaluated grouped by the dimensions it reaches and repeated on each row of the others; a filter on an unreached dimension is ignored for it (OBIEE: the measure's level set to Total for that dimension).

There is no "blank" option, because a blank cell reads as "no data". Use `total` on a separate metric, never on the base one, so the base keeps failing loudly: `company_busy_hours` repeats across stores so that `store_share_of_company_busy_hours` has a denominator, while `busy_hours` still errors by store.

### Weighted bridges

Crossing a `weight` relationship, a `SUM` metric is allocated by the weight; a derived metric is rebuilt from allocated inputs; a `NON_ADDITIVE` metric cannot be allocated, so the query fails. A member with no bridge row keeps its rows under a null bridge member at weight 1, so the bridge never drops a row.

### Dimensions held at several grains

A dimension can have several physical tables at different levels: a day calendar and a month calendar, or a customer table and a customer-segment table (OBIEE: several logical table sources on one logical dimension table, each with its own content level). The row-level table is the detail source. Each coarser table is a `priority_group: 0` source of the same dataset whose `content_levels` names one of the dataset's own levels, with no `via`, and the `key_columns` that carry that level's key. It may map only the fields that level determines: its keys and attributes and those of every coarser level (`own-level-finer-field`). An aggregate at that level then joins the coarser table instead of the row-level one, and `validate` accepts either join. The star example shows a month table beside the day table.

### Which ratio is meant

| Question | Shape | Example |
| --- | --- | --- |
| Ratio of totals (weighted by the denominator) | `derived_expression` over two metrics | `average_order_value`, `utilisation_rate` |
| Average of a row-level ratio | Base metric whose core expression is `AVG(a / b)` over row fields | — |
| Average of per-group ratios (each group weighs the same) | `based_on_dimensions` of the ratio metric, `rule: AVG`, `across` the group level | `mean_store_average_order_value`, `mean_employee_utilisation_rate` |
| Typical or extreme period | `based_on_dimensions` across a time level with `AVG`, `MAX`, `MIN` or `MEDIAN` | `avg_daily_order_revenue`, `peak_day_order_count` |
| Opening or closing value of a period | `based_on_dimensions` across a time level with `FIRST` or `LAST` | `closing_active_employee_count` |

Name the weighting in the description whenever a weighted and an unweighted figure both exist: they answer different questions and read alike.

## Values and expressions

The schema constrains values as well as keys, and `validate` reports a value that breaks a constraint with one code per JSON Schema keyword (`vibedata/schema-anyof`, `vibedata/schema-pattern`, `vibedata/schema-minlength`).

| Value | Rule |
| --- | --- |
| Every name, handle and reference (`$defs/identifier`) | An Ossie SQL identifier, per Ossie's expression language: a regular identifier (`^[A-Za-z_][A-Za-z0-9_]*$`, at most 128 characters, matched case-insensitively), or an ANSI double-quoted one (a doubled quote escapes one) for a physical name that needs quoting, such as a `column_map` target with a space. Prefer regular identifiers: they port |
| `physical_tables[].source` | `schema.table` or `catalog.schema.table`, each part an identifier |
| `vibedata_version` | The current key set, `"1.6"` (`"1.5"` is also accepted); a document wholly on another generation fails `vibedata/version-unsupported` once |
| `join_type` | `LEFT OUTER`, `INNER`, `FULL OUTER` or `RIGHT OUTER` (`vibedata/bad-join-type`) |
| `scd.open_ended_value` | An ISO date, `YYYY-MM-DD` |
| `note`, `role` | Non-empty when present |

Every expression is parsed by Ossie's own `validate_sql_expression` and then checked for its kind, which the schema names with the annotation `x-ossie-expression-kind` (JSON Schema ignores it; `validate` enforces it):

| Kind | Where | Rule |
| --- | --- | --- |
| `predicate` | `content_filter`, metric `filter`, `join_expression` | Boolean at its root: a comparison, `AND`/`OR`/`NOT`, `IS [NOT] NULL`, `IS [NOT] DISTINCT FROM`, `IN` with a value list, `BETWEEN`, `LIKE`/`ILIKE`, a boolean function or a bare boolean column. No aggregate, window function or subquery (`vibedata/content-filter-kind`, `vibedata/filter-kind`, `vibedata/join-expression-kind`) |
| `metric-formula` | `derived_expression` | Arithmetic over metric names and scalar functions (`NULLIF`, `COALESCE`, `CASE`, `CAST` and the like), never a predicate. No aggregate, window function or subquery (`vibedata/derived-kind`) |

Ossie core's own expressions (the `ANSI_SQL` and `OSSIE_SQL_2026` dialects only) are held to what the Ossie spec says and its validator does not yet enforce: a metric expression aggregates (`ossie/metric-not-aggregate`) and a field expression does not (`ossie/field-aggregate`). A call to a function outside the spec's REQUIRED and RECOMMENDED lists warns (`ossie/function-unlisted`): the expression may be valid in one engine, but Ossie does not promise it ports.

## Upgrades

| Version | What moved | Why |
| --- | --- | --- |
| `1.1` | `logical_sources[].where` removed | It was prose; a population is a decision (ADR) held by a test, not a sentence |
| `1.2` | Added `variables`, `content_levels`, `content_filter`, `navigable`, metric payloads (`aggregation`, `derived_expression`, `at_levels`, `time_series`, and a two-stage `nested` rule); hierarchy levels became `{name, key, label}` objects with `is_time` on the hierarchy; date gained `month_start_date` and `week_start_date` | An engine could not pick an aggregate (grain was prose), could not tell a windowed aggregate from the full fact (the aggregates silently covered fewer rows than the detail), keyed levels on non-unique columns (`calendar_month`, a shared member name), and re-summed ratio columns. `content_filter` is the machine-checked successor of `where` |
| `1.3` | Levels moved out of hierarchies into the dataset's `levels[]`, each with `keys[]` (`{name, fields, primary, display}`) and `attributes[]`; hierarchies list level names and, on Type 2 dimensions, `scd_rollup`; added `row_level`; level references dropped `hierarchy` and gained `key` and `key_columns`; `nested` became `based_on_dimensions` (`over`→`across`, `outer`→`rule`) and lost `empty_members`; added `ossie.py level-tests` (since merged into `generate-tests`) | A level had one key slot and a `label` of undefined meaning, so a repeating name could pass as a key. An aggregate's level had no join key, so it could not be joined to its dimension at that level. A member and a table row were not told apart (a member versus its versions). `nested.empty_members: calendar` needed a densified member space, which is a cube concern this semantic layer does not take on |
| `1.4` | Added metric `filter` and `unrelated_dimensions`, `ROLLING` with `periods` on `time_series`, relationship `to_level` and `weight` (a weighted bridge), own-level `content_levels` on a dimension's coarser sources, and `ossie.py dimensionality`; a standalone bridge document folded into its star as a weighted bridge | A billable metric's population was hidden in its SQL, so no engine could match it to a filtered source. A query grouping a metric by a dimension its fact cannot reach was undefined. A bridge's weight was prose. Rolling windows existed only as row-counting boundary dbt model columns. A dimension with a month table had nowhere to declare it |
| `1.5` | Expressions are checked by Ossie's own `validate_sql_expression` and parsed in its generic dialect, with unquoted identifiers case-insensitive; `join_expression` became Ossie `dataset.field` grammar, parsed, resolved and used by the compiler, and every existing one that restated the core columns was removed; the unused dataset keys `alias_of`, `physical` and `partitioned_by` were removed and `partitioned_by` moved to `physical_tables[]`; document `variables` were removed, each `:variable` in a content filter becoming the literal its dbt var held, and a `:placeholder` is now an error; the payload groups are named by Ossie document component | Join expressions named columns neither boundary dbt model has, others restated the core columns, and nothing parsed them. Physical facts do not belong on a logical dataset. Variables are deferred until a consumer needs them. "Level" now means a dimension level only |
| `1.5` (validation) | No key moved. The schema now constrains values: identifiers, `schema.table` sources, the version constant, `join_type`, ISO `open_ended_value`, non-empty `note` and `role`; every expression carries its kind (`predicate` or `metric-formula`), checked by `validate`; metric expressions must aggregate and field expressions must not; functions outside Ossie's lists warn | 48 schema strings accepted anything, so a typo in a handle or a predicate written as arithmetic validated green until a consumer tripped on it |
| `1.6` | `conformed_from` on a dataset: a copy of a dimension names the document that owns it | A key was added, so the key set changed; a document wholly on `1.5` stays valid |
