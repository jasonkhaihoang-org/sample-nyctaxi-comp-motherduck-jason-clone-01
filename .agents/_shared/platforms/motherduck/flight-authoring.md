# MotherDuck Flight Authoring

The committed contract for a `<Name>.Flight/` item, under `orchestration/` or `ingestion/`.
`SKILL_DIR` below is `SKILL_DIR=<this skill's directory>`, the skill that sent you here; substitute it, the runtime does not expand it.

## The committed item

| Part | Holds |
| --- | --- |
| `flight.py` | one single-file program with `main()` and a `__main__` guard, copied from `./templates/flight-dbt.py`, or that body joined with an ingestion Flight's in one `main()` |
| `requirements.txt` | every dependency pinned `==`, resolved under the managed constraints |
| `config.json` | the declared non-secret key set, plus optional `flight_secret_names` and `schedule_cron` |

- One Flight per independently operated workload boundary, never one per dbt model; a combined dlt → dbt Flight only when both share interval, owner, failure boundary and recovery contract.
- Adapt a template by setting its constants and declaring its config keys; the checkout, the escalation and the workload invocation are the platform contract.
- Identity is the directory name: no `.platform`, no `logicalId`, no identity check on `modify`.
  The server `flight_id` is resolved at apply time and never committed (`committed-flight-id`).
- A content change creates a new Flight version; a `config.json`-only change does not.

## config.json is the declared key set

- Every environment name `flight.py` reads must be in `config.json`: `MD_RUN_FLIGHT` rejects a per-run override for an undeclared key.
- **Every key is declared with its production value**, plus `schedule_cron` unless the Schedule is `none`:

  | Key | Committed value | Overridden on an Intent run |
  | --- | --- | --- |
  | `GIT_REF` | the approved revision | the Intent's branch |
  | `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` (dlt) | the Domain's database | the Intent's ephemeral one |
  | `DLT_INGEST_LIMIT` (dlt) | `-1`, every row | a safety run's or sample load's row cap |
  | `DEV_MODE` (dlt) | `false` | `true` on a safety run |
  | `DESTINATION_DATABASE` (dbt) | the Domain's database | the Intent's ephemeral one |
  | `DBT_SCHEMA` (dbt) | the Domain's schema | the Intent's schema |

  Each key is the name its own tool reads; neither program reads one. A run may override a declared key and nothing else — `MD_RUN_FLIGHT` answers `config key "X" is not defined on this Flight`.
- Everything else is a constant in `flight.py`: the repository, the project subdirectory, the pipeline and connection names, the dbt selector. Declaring one lets a run build something nobody approved.
  `GIT_REPO` is the `<owner>/<repo>` of the Domain checkout's `origin` remote; when that remote names no GitHub repository, ask the user for it.
- Exempt runtime injections: `MOTHERDUCK_TOKEN`, `MOTHERDUCK_FLIGHT_ID`, `MOTHERDUCK_FLIGHT_RUN_ID`, `MOTHERDUCK_FLIGHT_RUN_NUMBER`, `HOME`.

## Dependencies come from the managed constraints

The runtime installs `requirements.txt` verbatim with no `-c`, so constrain when you write it.
List the Flight's packages and the Domain's connector requirements in `requirements.in`, write the constraints, and compile for the Flight runtime's Python:

```bash
python3 "$SKILL_DIR/../../scripts/runtime_pins.py" --platform motherduck --out /tmp/managed-constraints.txt
```

```bash
uv pip compile requirements.in -c /tmp/managed-constraints.txt --python-version 3.12 --no-header -o requirements.txt
```

- A dlt Flight names its dataset with `dataset("<logical>")` from `vibedata.dlt.core`, so list `vibedata-dlt-core` in `requirements.in`.
- `validate-flight.py` fails a managed package (dbt, dlt, adapters, `vibedata-*`) at any version but the managed one; never pick one by hand.
- Commit `requirements.txt`, not `requirements.in`.
- Pin `duckdb` at or above the constraints' floor: an older one dies at `duckdb.connect("md:")` with `Your DuckDB version is not supported by MotherDuck`, after the whole install.

## The dbt connection

The project's committed `transformation/profiles.yml` is what a dbt Flight builds under, and `requirements.txt` pins `dbt-duckdb`.
Never `type: motherduck`: it needs a separate adapter that fails dependency resolution.

Read the file when authoring orchestration:

- **No file, or no target reading `DESTINATION_DATABASE`** — tell the user, then create it from `./templates/dbt-profiles.yml`. `<profile_name>` is the fallback literal in `transformation/dbt_project.yml`'s `profile:` key.
- **A target holds a fixed database** — ask the user to make it `env_var('DESTINATION_DATABASE')`; do not rewrite it.

## Silent-green

A **silent-green** Flight reports success while its work was wrong; each case has a `validate-flight.py` rule.

1. **Workload failure does not fail the Flight.** Status reflects only whether Python raised, and neither engine raises: `dbtRunner.invoke` returns `success=False`, dlt reports `has_failed_jobs` and per-package `state`.
   Inspect the result and `sys.exit(1)` on failure.
2. **An unnamed database is not an error.** Unnamed, the Flight writes to `my_db`.
   Set `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` for dlt and `path: "md:<database>"` for dbt.
3. **A bare secret name resolves to the wrong secret.** A `flights` secret injects `<secret_name>_<PARAM>` and bare `<PARAM>`; the bare alias is last-attached-wins.
   Read only the namespaced name.
4. **An undeclared config key can never be supplied** (§ config.json).
5. **An undeclared credential is nobody's error.** `MD_CREATE_FLIGHT`, `MD_UPDATE_FLIGHT` and `MD_RUN_FLIGHT` reject a `flight_secret_names` entry with no account secret (`Catalog Error: user_secret not found`); an undeclared one is simply absent, and `os.environ.get()` skips the load and rebuilds on stale data.
   The platform checks a secret's name, never its `PARAMS` keys, so a missing key is also silent.
   Declare every credential and read each with `os.environ[...]` (`optional-secret-read`).
6. **A ref fixed in the program makes the sandbox prove nothing.** The sandbox and the schedule apply identical bytes and differ only in `GIT_REF`; fill it in the program and they build different trees (`pinned-ref`).

## Runtime traps

- **A dbt selector must cover what its tests reference:** a test on an excluded model fails on a missing relation; widen the selector.
- **Never create the destination database.** The configured value names one that already exists.

## The project is fetched, not carried

`vibedata.flight.checkout` places the project at `GIT_REF` and returns its directory; `flight.py` runs dbt or dlt against that path. Pack nothing into `source_code`.

## The git credential

`flight.py` declares `GIT_SECRET_NAME` and `GIT_SECRET_PARAM`; the runtime injects the pair as `<secret_name>_<PARAM>`. The platform checks a secret's name but never its parameter keys, so a wrong key applies and injects nothing.

- `GIT_SECRET_NAME` is `<domain slug, hyphens replaced by underscores>_git_auth`, **lowercase** — DuckDB stores an unquoted secret name lowercased, and `flight_secret_names` must match the stored spelling.
- Inside an Intent, write the secret with the pair the program declares, before **every** run — a brokered credential ages out between runs:

  ```bash
  bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" 'python3 "$SKILL_DIR/../../scripts/platforms/motherduck/resolve_creds_and_run.py" "CREATE OR REPLACE PERSISTENT SECRET <domain_slug>_git_auth (TYPE flights, PARAMS MAP{'"'"'GIT_TOKEN'"'"':'"'"'{{BROKER:github}}'"'"'})"'
  ```

  Write the credential as `{{BROKER:github}}`, never a value; the script resolves it in its own process.
- For a scheduled Flight the **Domain owner creates the secret by hand**, holding a long-lived credential they rotate — no agent runs beside a schedule to replace one. It must exist **before** CD applies the Flight: `MD_CREATE_FLIGHT` rejects a `flight_secret_names` entry with no account secret, so the apply fails, not the first run.

## Secrets

Workload credentials (a source's username, password, API key) reach a Flight as a MotherDuck `flights` secret, the same surface the git credential above uses. An ingestion Flight's source credentials take the secret and parameter names `./dlt.md` § Source secrets derives, so none is asked for; the rest of this section holds for them too.

- The user creates the secret in the MotherDuck UI before apply; ask for parameter names where `flight.py` reads them itself, never values, and hand over the link as a titled hyperlink:

  ```text
  [MotherDuck → Settings → Secrets → create `<secret_name>`](https://app.motherduck.com/settings/secrets?action=create&type=flights&name=<secret_name>&params=<PARAM>,<PARAM>)
  ```

- `params` holds names only, comma-separated, and must be exactly the names `flight.py` reads (silent-green 5) — for a source secret, exactly the parameters `./dlt.md` § Source secrets derives; say them in your message.
- Never write out a `CREATE PERSISTENT SECRET` holding a value; it puts the credential in the transcript. A statement whose credentials are `{{BROKER:<audience>}}` placeholders holds none, which is what `resolve_creds_and_run.py` above takes; one whose values are `<value>` placeholders is what the user runs. One `PARAMS` of type `MAP(VARCHAR, VARCHAR)`, persistent; named parameters like `PASSWORD` are rejected. For a source credential the names come from `./dlt.md` § Source secrets:

  ```sql
  CREATE PERSISTENT SECRET sources__sf_prod__credentials (TYPE flights, PARAMS MAP{'CLIENT_ID': '<value>', 'CLIENT_SECRET': '<value>'});
  ```

  ```text
  [MotherDuck → Settings → Secrets → create `sources__sf_prod__credentials`](https://app.motherduck.com/settings/secrets?action=create&type=flights&name=sources__sf_prod__credentials&params=CLIENT_ID,CLIENT_SECRET)
  ```

- List every credential the Flight needs in `flight_secret_names` — the workload's, **and the git secret from § The git credential**. The runtime injects a secret's parameters only for a name listed there, so an omitted one is an absent variable at run time rather than anything the platform reports. What to do when apply rejects one is `./flight-sandbox-run.md` step 2.

## Target authentication

The runtime injects `MOTHERDUCK_TOKEN` under the Flight's own identity (`access_token_name`, default `MotherDuck Flights`).
Never put a token in `config.json` or the program.

## Schedules are authored, never activated

- Declare `schedule_cron` as five-field **UTC** cron when the design approves a cadence; it is held back from applied `config` and attached by customer CI/CD.
- `Scheduled runs are not available on your plan` is expected below the Business plan: record the cadence and carry on; never propose an upgrade, another scheduler or an unscheduled Flight.
- Convert local time to UTC yourself and say so; a UTC cron cannot follow daylight saving, so name the one-hour seasonal drift and let the user pick.

## Gate

```bash
python3 "$SKILL_DIR/../../scripts/platforms/motherduck/validate-flight.py" <dir>/<Name>.Flight --repo-root .
```

Exit 0 is required before apply or commit; fix findings, never work around the validator.
