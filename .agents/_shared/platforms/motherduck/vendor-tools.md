# MotherDuck Vendor Tools

Native `lakehouse_schema` and `lakehouse_query` are the query surface; vendor tools are for what only they cover.
Nothing structural blocks a vendor write (`platform-tools.json` is checked only by evals), so this file is the guard.

## Use these

| Need | Tool |
| --- | --- |
| Real identifiers and types | native `lakehouse_schema` |
| Bounded read-only probes | native `lakehouse_query` |
| Vendor catalog search | `search_catalog` |
| Views, macros, shares | `list_views`, `list_macros`, `list_shares` |
| Table or column listing native schema cannot give | `list_tables`, `list_columns` |
| Apply or run a committed Flight | `list_flights`, `create_flight`, `update_flight`, `run_flight` |

- Read schema from live tables, never from memory or guessed column names.
- Flight tools carry only `source_code` / `requirements_txt` read from the committed, validated `orchestration/<Name>.Flight/` (`./flight-sandbox-run.md`).
  Never compose Flight source inside a tool call; with no committed item, author one with `generating-orchestration` first.
- `MD_CREATE_FLIGHT` and the other SQL functions are customer CI/CD's interface; the agent's placeholder token cannot use them.

## Never use these

| Tool | Why |
| --- | --- |
| `query_rw` | dbt and dlt are the only write path; probe with `lakehouse_query`, vendor `query` only for what native cannot express |
| Dives (`save_dive`, `dive_query`, `view_dive`, …) | live outside the repository; a dashboard request is still a dbt model |
| Guides (`create_guide`, `update_guide`, `set_guide_access`, …) | documentation belongs in the repository |
| `get_short_lived_token` | credentials are resolved for you |
| `delete_flight`, `delete_dive`, `delete_guide` | destructive and irreversible; never speculatively |
