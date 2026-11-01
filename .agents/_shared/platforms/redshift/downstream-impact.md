# Downstream impact testing

The sandbox holds only what this Intent built, so stage one alias per unbuilt Domain relation the consumer reads.
Run every statement with `lakehouse_query` on `ephemeral`, one per call; never write with `domain`.

`SKILL_DIR` in the command below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

## List

`lakehouse_schema` on `ephemeral` with `schemaName`, once with `objectType: tables` and once with `objectType: views`, before staging and after cleanup; without `schemaName` system views dominate.
A listing with `capReached` true is not the whole catalog: narrow it, one `schemaName` at a time, until it is false.
Without native schema tools, use `./dialect.md` § Schema fallback.

## Stage

1. Write the before-staging listing, one `schema.table` per line, into `.agents_tmp/built.txt`.
2. Name the unbuilt relations the consumer reads, never from memory. For a dbt consumer, give its `unique_id` in the production manifest; when `/data/cache/prod-target/manifest.json` is absent, or the consumer has no dbt graph, name each relation from its own SQL with `--relation <database>.<schema>.<table>` (repeatable) instead.

   ```bash
   SKILL_DIR="<this skill's directory>" && python3 "$SKILL_DIR/../../scripts/platforms/fabric_warehouse/unbuilt_relations.py" --prod-manifest /data/cache/prod-target/manifest.json --consumer <consumer unique_id> --built .agents_tmp/built.txt
   ```

   It prints a sorted JSON array of `database.schema.table` names the consumer reads and the sandbox lacks. An empty array means nothing needs staging; a non-zero exit means the manifest or the consumer was not found, so report its message rather than guessing.
3. Per printed `<database>.<schema>.<table>`, keeping its database:
   `CREATE VIEW <schema>.<table> AS SELECT * FROM <database>.<schema>.<table> WITH NO SCHEMA BINDING`
   - Plain `CREATE VIEW`, never `CREATE OR REPLACE`: its `already exists` refusal protects an existing relation; do not retry that name.
   - `WITH NO SCHEMA BINDING` is required across databases.
   - If the schema is absent, `CREATE SCHEMA <schema>` first and record it as created.

## Cleanup

- `DROP VIEW <schema>.<table>` for exactly the aliases this test created; the before-staging listing tells an alias from a built view.
- Then `DROP SCHEMA <schema>` for each created schema, without `CASCADE`.
- List again and confirm every pre-existing relation remains.
