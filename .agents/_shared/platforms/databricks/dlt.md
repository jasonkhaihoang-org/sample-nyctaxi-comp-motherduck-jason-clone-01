# Databricks dlt

Dialect: `./dialect.md`.

## Authoring

- The pipeline is a Databricks notebook, `ingestion/<name>_pipeline.ipynb`, from `./templates/dlt-pipeline.ipynb`; never write `ingestion/<name>_pipeline.py`. The rest of the layout (`sources/`, `requirements.txt`) is unchanged.
- A notebook is executed, never imported: its cells run top to bottom, the load flat in the last one, so the `main()` boundary does not apply; validate it by reading.
- An existing notebook missing a widget the template has is brought up to the template before its next run.
- Fill the first cell's `pipeline_name` and `connection_name` defaults; leave the other widgets as the template has them. The notebook names no host, catalog, warehouse, schema or secret: the catalog and warehouse arrive in its `dlt_env` widget (§ Destination), through which a sandbox run also sets the Intent's schema prefix.
- The destination is `databricks_files_api()` from `vibedata-dlt-databricks-notebook`, exactly as the template builds it, never dlt's own `databricks` destination.
- The install cell names `"dlt[databricks]"` and `pyarrow` itself and installs under the Domain's `.github/managed-constraints.txt`; add a connector dependency to `ingestion/requirements.txt`, never to that cell.

## Pipeline artifact

The artifact is `ingestion/<name>_pipeline.ipynb`; the audit reads its code cells. The runtime wrapper is the template's: `setup_environment()` and the Secret Store providers in their own cell, and `finalize` is `vibedata-dlt-core`'s `persist_audit(pipeline, pipeline.last_trace)`, on success and, with `error_message`, on failure before the re-raise. The last cell fails the run when a job failed or a package did not load, and only past that check exits with the `destination-identity:` line, reading the catalog from dlt's own connection and naming the dataset it loaded; a catalog it cannot read prints `destination-identity unavailable` and emits no line. The template's row cap and dev mode are its `dlt_ingest_limit` and `dev_mode` widgets, so neither is hard-coded. dlt creates its staging volume inside the schema it loads into. The widget and `%pip` cells are exempt from the pipeline audit's runtime-contract rule, and `persist_audit` stands in for its `finalize`. Keep the template's cells and order; author only the source, resources and hints.

## Destination

`databricks`, the name of the `databricks_files_api` destination the pipeline notebook (`./templates/dlt-pipeline.ipynb`) builds; Databricks compute supplies the host and credential, so no auth method applies. Merge `./templates/dlt-config.toml` into `ingestion/.dlt/config.toml`, leaving a key already present as it is: it holds the recommended settings and no `[destination.databricks.credentials]`, which dlt refuses in `config.toml` (`ValueNotSecretException`); remove one an older template left. The catalog and SQL warehouse reach the notebook through its `dlt_env` widget: the job passes its `dlt_env` variable, which defaults to the catalog and warehouse the job is deployed with, and a sandbox run passes the Ephemeral ones. A committed host would override the notebook's own workspace, so none is committed.

## Secret Store

Unity Catalog secrets, kind `databricks_uc_secrets`, are the one Secret Store this platform's runs read. A Domain bound to any other kind, such as a workspace secret scope, is moved to Unity Catalog secrets by a Domain Owner in the Domain's settings.

## Unity Catalog secrets

Hand over, per absent name, its creation in the schema `<catalog>.<schema>` (Catalog Explorer, or the Unity Catalog secrets API; the user types the value there, never in chat) and https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets. A Domain Owner then grants `READ SECRET` on each secret to the user and to the Domain service principal (it cannot be granted on the schema), plus `USE CATALOG` and `USE SCHEMA` on its path. The run reads each value with `dbutils.secrets.get(catalog=, schema=, key=)`, which needs Databricks Runtime 17.3 LTS or newer, or serverless environment 4 or newer.

## Sandbox run

The load runs on Databricks serverless compute, never in this container. Commit first: the run uploads the repository as it is on disk (minus `.gitignore`d files) to the user's workspace folder for this Intent, then runs the notebook once with its committed widget values, overriding only the row cap and dev mode, and passing the Ephemeral catalog and warehouse as dlt's `DESTINATION__DATABRICKS__CREDENTIALS__CATALOG` and `__HTTP_PATH`, the Intent's `VD_EPHM_SCHEMA_PREFIX` and Studio's `DESTINATION__STAGING_DATASET_NAME_LAYOUT`, in `dlt_env`. `SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

```bash
cd /workspace && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" \
  'python "$SKILL_DIR/../../scripts/platforms/databricks/run_notebook.py" --notebook ingestion/<name>_pipeline.ipynb --log <log> --limit <N> [--dev-mode]'
```

- This command is the safety run (`--limit 1 --dev-mode`) and a sample load (`--limit <N>`). A run lasts as long as its load: launch it with `start_async_bash` and `timeout_seconds: 3600`, with `$SKILL_DIR`, `<name>`, `<log>` and `<N>` substituted, and wait with `wait_for_async_bash`. Give each run its own `<log>` file, and pass it to the landing gate's `assert_destination.py --resolved-from-log`; never retype the identity it holds. Its `dataset` is the schema the run loaded, dev-mode suffix included: the `--dataset` for `run_bronze_tier1_tests.py`.
- Exit 1 (`RUN_FAILED`) is the run's own failure: the log carries its run URL, error and trace. Exit 2 (`RUN_NOT_STARTED`) is the environment: a missing coordinate, or a refused sync or submit. A permission, scope or credential error in either is the user's to fix: report the exact message and stop.
- A `ConfigFieldMissingException` names a dlt key: hand over that secret's creation as the Secret Store kind's `## Create` says; never an empty result. A permission error reading a secret the store lists means the run's identity holds `REFERENCE SECRET` without `READ SECRET` on it: the Domain Owner's grant to fix.
- A schema-contract violation on the second run is surfaced per the input rules of `../../references/guides/layer-roles.md`; never widen the contract silently.

## Full load

The full load is the `## Sandbox run` command with `--limit -1` and no `--dev-mode`: it loads everything into the Ephemeral catalog. The evidence is exit 0, then `audit_runs` in the loaded dataset (`<VD_EPHM_SCHEMA_PREFIX><dataset>`), read with `lakehouse_query` on `ephemeral`, showing this run with `first_run` true and a nonzero `total_rows_extracted`; a successful run that extracted nothing restored an earlier cursor and did not load. Its exits are `## Sandbox run`'s: 1 is the run's own failure, at its run URL; 2 is the environment; a permission or scope error is the user's to fix.

## Destination identity

Report the type and the Ephemeral catalog the gate reports.

## Destination mismatch

The notebook loads into the catalog its `dlt_env` names, and the gate compares the catalog the run reports with `VD_EPHM_DATABRICKS_CATALOG`; on a mismatch, read the run's parameters at its run URL.

## Bronze tests

A pytest suite cannot reach the Ephemeral catalog's tables from here; record a Tier 2/3 suite's execution as deferred.

## Bronze preview

Reads every table in the Ephemeral catalog's schemas that start with the Intent's prefix; install nothing for it.
