# Orchestration — MotherDuck

The native item is `orchestration/<Name>.Flight/`; its contract is `./flight-authoring.md` and its run is `./flight-sandbox-run.md`.
`SKILL_DIR` below is `SKILL_DIR=<this skill's directory>`, the skill that sent you here; substitute it, the runtime does not expand it.

The gate, used by Plan, Authoring, Evaluate and Document:

```bash
SKILL_DIR="<this skill's directory>" && cd /workspace && python3 "$SKILL_DIR/../../scripts/platforms/motherduck/validate-flight.py" orchestration/<Name>.Flight --repo-root .
```

It checks committed shape, pinned requirements, declared config keys, explicit destination database, workload-result propagation, namespaced secret reads, embedded secrets, committed Flight ids and cron shape.

## Intent

One native item, so no target choice and no platform branch.

## Design

Zero, one or several Flights in dependency order, one per independently operated workload boundary (`./flight-authoring.md` § The committed item).
Read `Flight` for `Orchestration Pipeline`; a row's `Target` is `flight`.

## Plan

| Action | Steps | Gate |
| --- | --- | --- |
| `create` | Generate → Sandbox run | validator exit 0, then a green run |
| `modify` touching `flight.py`, `requirements.txt` or the invoked dbt project | Generate → Sandbox run | as `create` |
| `modify` touching only `schedule_cron` | Generate | validator exit 0; no run, the sandbox never activates a schedule |
| `delete` | Remove | directory gone and removal commit cited from `git log` |
| `recreate` | Remove → Generate → Sandbox run | as `create` |

- Generate and Sandbox run are `generating-orchestration` steps; record each gate in the Plan's `## Execution evidence`.
- No identity check on `modify`, and no halt for a missing `.platform`.

## Verify

The validator per committed item, plus the green run evidence object; a `modify` row is covered by its gate outcome.

## Ship

- Customer CI/CD deploys with `MD_CREATE_FLIGHT` / `MD_UPDATE_FLIGHT`.
- A cadence needs a Business plan on the customer's account, so a committed `schedule_cron` may be inert; never alter the artifact for it.

## Authoring

Follow `./flight-authoring.md`: copy the template, author pinned `requirements.txt` and `config.json`, then run the gate until exit 0.

```bash
cp "$SKILL_DIR/../../_shared/platforms/motherduck/templates/flight-dbt.py" orchestration/<Name>.Flight/flight.py
```

A dlt workload has no template here: `generating-dlt-pipeline` authors its Flight under `ingestion/` and proves it by running it. Scheduling that Flight from orchestration is not wired yet — every surface in this file addresses `orchestration/<Name>.Flight/` — so a dlt cadence is a gap to report, never an item to author here.

## Sandbox run

Follow `./flight-sandbox-run.md`.
Green = terminal status **and** `exit_code 0` **and** the workload's result line; MotherDuck reports `RUN_STATUS_SUCCEEDED` with `exit_code 0` for a failed dbt graph unless the program escalates.
Static validation is not run evidence.

## Evaluate

A `RUN_STATUS_SUCCEEDED` with non-zero `exit_code` or no workload result line is a **critical finding**, not a pass (silent-green).

## Document

- Read `flight.py` and `config.json`; the committed program is complete as it stands, and the revision a run built is in that run's own logs, not in the artifact.
- `schedule_cron` is five-field **UTC** and needs a Business plan, so never describe it as running.
- Convert it to the Plan's local time (show the arithmetic) before comparing; halt for a conflict only if the converted time still disagrees.
- Validate each documented item with the gate above.
