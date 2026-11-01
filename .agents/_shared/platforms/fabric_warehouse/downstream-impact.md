# Downstream impact testing

An Ephemeral Warehouse holds views only for the relations this Intent built. A downstream consumer that reads an unbuilt Domain relation joins nothing until an Alias View to that relation exists. Create one Alias View per unbuilt relation the consumer reads, and name those relations with the script below rather than from memory.

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

## Stage

1. Write what the Ephemeral Warehouse already holds: `lakehouse_schema` on `ephemeral`, once with `objectType: tables` and once with `objectType: views`, one `schema.table` per line into `.agents_tmp/built.txt`. Page each listing until `capReached` is false: a capped page is not the whole catalog, and a missing name there would stage an alias over a relation the Intent built.
2. List the unbuilt relations the consumer reads. For a dbt consumer, name its `unique_id` in the production manifest; defer is unavailable when `/data/cache/prod-target/manifest.json` is absent, and then every relation is named with `--relation <database>.<schema>.<table>` instead (repeatable), as it is for a consumer with no dbt graph; take the names from the consumer's own SQL or the Intent's `target/manifest.json`, never from memory.

   ```bash
   SKILL_DIR="<this skill's directory>" && python3 "$SKILL_DIR/../../scripts/platforms/fabric_warehouse/unbuilt_relations.py" --prod-manifest /data/cache/prod-target/manifest.json --consumer <consumer unique_id> --built .agents_tmp/built.txt
   ```

   It prints a JSON array of `database.schema.table` names, sorted, each read by the consumer and absent from `.agents_tmp/built.txt`. An empty array means nothing needs staging; a non-zero exit means the manifest or the consumer was not found, so report its message rather than guessing the list.
3. `create_alias_views` — pass each printed name as a `source`, with the same name minus its `database.` part as the `alias`, at most 50 views per call. A name already holding a view is returned under `alreadyPresent` and a name a table holds is refused: report either rather than replacing it.

## List

- `lakehouse_schema` with `objectType: views` on `ephemeral` — list the views present before staging and again before cleanup, so the removal step touches only what this test created.

## Cleanup

- `delete_views` — remove every Alias View this test created before returning to build. Leave any view that was already present untouched.
