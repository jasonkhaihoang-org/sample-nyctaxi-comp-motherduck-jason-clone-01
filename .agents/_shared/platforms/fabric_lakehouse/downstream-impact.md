# Downstream impact testing

An Ephemeral Lakehouse holds only the relations this Intent built. A downstream consumer that reads an unbuilt Domain relation joins nothing until a shortcut to that relation exists. Stage one shortcut per unbuilt relation the consumer reads, then refresh the SQL metadata so the Lakehouse exposes the new relation to `lakehouse_query`. Stage before the first query: a relation absent from Ephemeral cannot be read until its shortcut exists, so a probing query beforehand only fails; a shortcut create that fails is the result to report, never a reason to skip staging the rest.

## Stage

- `create_shortcuts` — create a shortcut in the Ephemeral Lakehouse for each Domain relation the consumer reads that is absent from Ephemeral.
- `refresh_sql_metadata` — after creating the shortcuts, refresh the Lakehouse SQL metadata so the new relations are queryable before the consumer runs.

## List

- `list_shortcuts` — list the shortcuts present before staging and again before cleanup, so the removal step touches only what this test created.

## Cleanup

- `delete_shortcuts` — remove every shortcut this test created before returning to build. Leave any shortcut that was already present untouched.
