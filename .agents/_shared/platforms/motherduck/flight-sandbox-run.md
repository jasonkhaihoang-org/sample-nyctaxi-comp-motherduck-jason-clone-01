# MotherDuck Flight — Sandbox Run

Applies a committed `orchestration/<Name>.Flight/` to the sandbox and runs it on demand; the item contract is `./flight-authoring.md`.
Production deploy, schedule activation and production runs belong to customer CI/CD.

## Before anything

`VD_EPHM_MOTHERDUCK_DATABASE` unset means no sandbox: halt and report, never improvise a destination.

## The sequence

Only the validator is a script; apply and run go through the MotherDuck Flight tools, because the agent's `motherduck_token` is a placeholder (`./dialect.md` § Credentials).

**1. Gate the committed item** to exit 0:

```bash
SKILL_DIR="<this skill's directory>" && cd /workspace && python3 "$SKILL_DIR/../../scripts/platforms/motherduck/validate-flight.py" orchestration/<Name>.Flight --repo-root .
```

**2. Apply**, passing the committed files' contents:

- Flight name = directory name without `.Flight` (`orchestration/daily_revenue.Flight/` → `daily_revenue`).
- `list_flights` first, then `create_flight` if absent or `update_flight` if present; the item commits no id.
- `source_code` ← `flight.py` verbatim; fill nothing in.
- `requirements_txt` ← `requirements.txt` verbatim.
- `config` ← `config.json` **verbatim**, with two removals and nothing changed:
  - `schedule_cron` is held back.
  - `flight_secret_names` is held back from `config` and passed as the tool's own `flight_secret_names` argument, an array of names.
- Change no committed value. The sandbox aims the **run** (step 3), not the apply.
- Any change to the item is a change to the committed file, re-entering at step 1.

**A rejected apply naming a secret (`Catalog Error: user_secret not found`) is the credential handoff.** The git credential is yours to create — `./flight-authoring.md` § The git credential — then apply again. A workload credential is the user's: hand over the link from `./flight-authoring.md` § Secrets, wait for confirmation, apply again.
Never drop the name from `flight_secret_names`; that turns the rejection into a green run over no ingestion (silent-green 5).

**3. Run.** Rewrite the git secret first — a brokered credential ages out between runs, so a Flight that ran an hour ago fails at checkout now (`./flight-authoring.md` § The git credential). Then `run_flight`, overriding the target and the ref for this Intent, poll `get_flight_run` / `list_flight_runs` until `ended_at` is stamped, and read `get_flight_logs`.

- `config` on the run is a **merge**; a key you do not name keeps its committed value. Override, using the names this Flight declares (`./flight-authoring.md` § config.json):
  - its database key ← `VD_EPHM_MOTHERDUCK_DATABASE`
  - `DBT_SCHEMA` ← the Intent's schema, for a dbt Flight
  - `GIT_REF` ← the Intent's branch
- Omit the database key and the run builds the Domain's.
- A backfill or recovery is the same mechanism with a different ref.
- These are MCP tool calls running on MotherDuck, taking minutes: never use `start_async_bash` / `wait_for_async_bash`, and never launch a second `run_flight` for the same change.
- `../../../scripts/platforms/motherduck/flight_lifecycle.py` is the customer-CI equivalent over SQL functions; it will not authenticate here.

## The gate

- Green = terminal `SUCCEEDED` **and** `exit_code 0` **and** the workload's own result in the logs.
- Status appears bare (`FAILED`) or prefixed (`RUN_STATUS_FAILED`); match either, and treat `ended_at` as the end signal.
- A green record over a `dbt FAILED` log line is silent-green, not evidence.
- Logs arrive incrementally after `ended_at`: an empty or partial read is not an answer.
  Wait for the terminal line the template prints last — `dbt succeeded: <commands>` for dbt, `destination-identity:` for dlt, which follows the `LoadInfo` and the audit. The dbt node count is printed on the failure path too, so it is not the green signal. Never record evidence from a log without the terminal line.
- A non-green run returns to the committed file: edit, re-validate to exit 0, apply, run again; only a validator-passed version counts.
- Record the Flight name, applied version, run number, terminal status, exit code and workload result line.

## Reads that answer instead of failing

| Read | Actually returns |
| --- | --- |
| `get_flight_logs` after `ended_at` | nothing, then a partial log |
| `list_flights`, `get_flight` | `flight_secret_names` as `null` even when attached; no payload |
| `MD_LIST_FLIGHT_VERSIONS` | real `flight_secret_names`; no `source_code` column |
| `MD_GET_FLIGHT_VERSION` | the payload, byte-identical |

- Version records are immutable applied-time snapshots, not what is attached now.
- Resolve `current_version` from `get_flight` before reading a version; a fixed version number passes silently against a stale payload.
- `MD_GET_FLIGHT_VERSION` takes `version_number`, not `version`.

## Boundaries

- Sandbox database only; never the Domain database.
- Never activate a schedule.
- Never read, print, export or pass a credential on a command line.
- Never hand-patch the deployed Flight or run the workload outside its Flight.
- On a permission error, report and stop; the Business-plan `schedule_cron` refusal is expected.
