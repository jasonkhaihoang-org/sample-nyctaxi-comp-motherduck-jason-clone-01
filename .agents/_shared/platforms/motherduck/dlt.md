# Sandbox run — dlt on MotherDuck

## Authoring

- Template: `./templates/dlt-pipeline.py`; for a `dlt-builtin` `filesystem` connection, `./templates/dlt-pipeline-local-files.py`, a one-off load orchestration never invokes.
- Destination literal: `"motherduck"`; `pipeline.run(source)` with no `table_format`.
- The template's `columns: evolve` holds until the first full load; flip it to `freeze` after that load.
- **Never the `duckdb` destination:** it treats `credentials="md:<db>"` as a path and writes a local file named `md:<db>` while reporting `LOAD OK`.
  The generated file names no database: `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` is a declared config key and dlt reads it itself.

## Pipeline artifact

The artifact is `ingestion/<name>_pipeline.Flight/`: the pipeline is the Flight.
It holds `flight.py` from `./templates/dlt-pipeline.py`, `config.json` from `./templates/dlt-flight-config.json`, and `requirements.txt` — every dependency pinned `==`, including `vibedata-motherduck-flight`, `vibedata-dlt-duckdb-core` and `pyarrow` (the destination writes parquet). The committed shape `./flight-authoring.md` governs.
Each `config.json` value is the one production runs with; a sandbox run overrides them per run, and a key absent here can never be overridden.
`vibedata.flight.checkout` places the vendored connector and `.dlt/config.toml`; `PROJECT_SUBDIR` is `ingestion`.
`flight.py` alone is exempt from the pipeline audit's runtime-contract rule: it calls no `setup_environment()`, which mints a brokered credential and binds this container's ephemeral destination — a Flight has neither. The destination comes from a declared config key dlt reads itself.
Source credentials: `./templates/dlt-pipeline.py` registers their provider after `checkout()`; keep that order. `flight_secret_names` lists the git secret and the `CONNECTION_NAME` entry of `ingestion/.dlt/.flight-secret-names.json` (§ Source secrets). A credentialed connection with no entry there: run `add-or-update-source` in test mode for it.
Run `./flight-authoring.md`'s gate against it until exit 0.

## Destination

`motherduck`. Recommended auth method `mother_duck`, a MotherDuck PAT: on a Flight leave `password` empty, and dlt reads the Flight's own `MOTHERDUCK_TOKEN`.

## Sandbox run

The load runs on the Flight, never in this container. (The local-files route is the exception: its source is a file only this container holds, so it runs here on the skill's own command.) Push the branch once after scaffolding, so the checkout finds the connector and `.dlt/config.toml`, then iterate:

- `update_flight` with `flight.py`'s current text, `requirements.txt` verbatim, and `config.json`'s committed values. The program is the argument, so an edit needs no commit.
- `run_flight`, overriding `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` with `VD_EPHM_MOTHERDUCK_DATABASE`, `GIT_REF` with the Intent's branch, and `DLT_INGEST_LIMIT` with the step's row cap — a safety run's `1`, a sample load's `<N>`, omitted for a full load; the safety run also overrides `DEV_MODE` with `true`, so it lands in a throwaway copy of the dataset that step 10's drop command removes. A key the apply did not declare is refused, and one this omits keeps its committed value.
- Then read `get_flight_logs` — logs arrive incrementally and lag the terminal status by a few seconds, so an empty read is not an answer.
- Save the run's final `get_flight_logs` read to its own file and pass it to step 9's `assert_destination.py --resolved-from-log`. The gate finds the run's own `destination-identity:` line there; it refuses a log without one, because the program emits it only past its own success check. Never retype the identity — a hand-written one asserts what you believed, not what the run did.
- A dependency added mid-loop goes into `requirements.txt` as well, or the next apply resolves differently from the last run.
- Commit `flight.py` when the program is final: what orchestration picks up is the committed artifact, not the applied one.

- A credential, permission or client-version error from the load is an environment failure: report the exact message and stop.
- A `ConfigFieldMissingException` in the logs names a dlt key: its secret absent from `flight_secret_names` → add it; present → the parameter is absent from the store, hand over its creation (§ Source secrets). Never an empty result.
- In this container (the local-files route only) secrets resolve as `## Provider config` in `../../secret-stores/<secret-store>.md` says.
- The sandbox is a Domain clone: take evidence from the load package and audit tables, not from tables existing.
- `finalize()` is audit-only here.
- A schema-contract violation on the second run is surfaced per the input rules of `../../references/guides/layer-roles.md`; never widen the contract silently.

## Source secrets

A source credential is a MotherDuck secret of `TYPE flights`; the Domain's Secret Store kind is `motherduck_flight_secrets`, the only kind a Flight reads — a credentialed source under any other kind halts `SECRET_STORE_KIND_UNSUPPORTED`.

- A dlt key's secret and parameter are what `## Name shape` in `../../secret-stores/<secret-store>.md` gives; the run reads `<secret>_<PARAMETER>`.
- `list_secret_names` returns `<secret>_<PARAMETER>` for every parameter the account holds, never a value: the inventory and the re-check; compare exactly.
- Hand over the statement with `<value>` placeholders and the link with the names filled in (`./flight-authoring.md` § Secrets); never a value, never create it yourself.
- Names are global to the MotherDuck account.
- On `NAMES-PRESENT`, write the connection's secret names to `ingestion/.dlt/.flight-secret-names.json` as `{"<connection>": ["<secret>", …]}`, replacing that connection's entry (git-ignored). `generating-dlt-pipeline` copies them into `flight_secret_names`; where a Flight `config.json` binding this connection already exists, add them to its `flight_secret_names` now, keeping the other entries, and commit it with the connection.

## Destination identity

Report the bare catalog name dlt resolves, as the gate reports it — never a path, never an `md:` prefix you added.

## Destination mismatch

A `destination ... differs from ... and will be ignored` or `state differs` warning means the load hit a local file or another catalog.

## Bronze tests

A pytest suite cannot connect here (placeholder token); record a Tier 2/3 suite's execution as deferred.

## Bronze preview

Reads the Ephemeral MotherDuck database over `md:`. Nothing of the load reaches this container's filesystem, and a `data/*.duckdb` file found here is a stale local artifact, never this platform's evidence.
