# Orchestration sandbox run — Fabric

The Fabric sandbox run of `generating-orchestration`, shared by both Fabric platforms; a committed `.ApacheAirflowJob` takes the Airflow section below.
Deploy the committed `orchestration/<Name>.DataPipeline/` and the notebooks it invokes into the **ephemeral** workspace and run it on demand to a terminal status.
Compose the single-capability scripts; there is no workflow script, and nothing is regenerated from a design record.
Production deploy, schedule activation and production execution are customer CI/CD's.

**The gate is always the pipeline run**, plus the dbt job notebook's evidence for every dbt activity; running a notebook alone is a diagnostic, never the gate.

## Process

0. The capability scripts and references live in the **plugin**, never in the Intent repository, so never `find` them under `/workspace`. List them once:

   ```bash
   SKILL_DIR="<this skill's directory, from the footer>" && ls "$SKILL_DIR/../../scripts/platforms/_family/fabric"
   ```

   `validate_shell_script` cannot inspect plugin scripts; validate any workspace-owned `.sh` or `.bash` script immediately before executing it.

1. Read `./capabilities.md`, then **deliver** each engine's code to `Files/<slug>/<subdir>/` in the Lakehouse its notebook is attached to. For **dlt**, upload `ingestion/`: the upload retargets the committed destination ids (`[destination.filesystem]` on a Lakehouse Intent; `[destination.fabric]` on a Warehouse Intent, which needs `--warehouse-id` beside `--lakehouse-id` (the Ephemeral Paired Lakehouse)) to the ephemeral resource in the uploaded copy only, and on a Warehouse Intent a committed staging `[destination.filesystem] bucket_url` to the Ephemeral Paired Lakehouse's `Files/staging`, so the load lands where dbt reads.

   For **dbt**, upload `transformation/` (`./orchestration-sandbox-run.md` step 2) with the Intent's `~/fab_notebook_profile/profiles.yml` beside it. Pass `--prod-manifest /data/cache/prod-target/manifest.json` whenever that file exists; when it is absent, record "defer unavailable" in the evidence and deliver without it.

   Delivered means an `uploaded N files → Files/<slug>/<subdir>/` line per engine, and for dbt the Intent-profile line and, when passed, the manifest-copy line.

2. For each notebook the pipeline invokes, import the committed directory itself with `import-notebook.sh` and capture the id; the import attaches the ephemeral Lakehouse, which is the code path. The dlt item is `ingestion/<name>_pipeline.Notebook/` and each dbt job is `orchestration/<job>_dbt.Notebook/`; importing anything else leaves a `notebookId` unmapped and `prepare-ephemeral-import.py` stops. Never author or edit an item here. Imported means every `notebookId` in the pipeline has an id.

3. Remap the committed pipeline's portable references with `prepare-ephemeral-import.py` into a temp copy (never edit the repo copy), import it, and run it, per `./orchestration-sandbox-run.md`. Never hand-author pipeline JSON or `fab` commands. Never activate a schedule.

   **The run outlives a terminal call.** Launch `bash "$SKILL_DIR/../../scripts/platforms/_family/fabric/run-item.sh" "<name>" DataPipeline` with `start_async_bash` and `timeout_seconds: 1800` (default 300; a Lakehouse run is slower because each dbt command opens its own Spark session), substituting `$SKILL_DIR` and `<name>` first because the async shell inherits no variables. Wait with `wait_for_async_bash` and `wait_timeout_seconds: 300`. `running` means still live; `timed_out`, `cancelled`, `failed` or `failed_to_launch` means the local command ended. Then read the remote run with `fab job run-status "<ws>.Workspace/<Name>.DataPipeline" --id <instance-id>` (status, failure reason, start and end time), never the last output line. Never launch `run-item.sh` a second time for the same change: concurrent runs replace the same tables.

4. Apply the skill's initialization-marker step to the write command itself.

5. Report the imported items, the invoked engine subset and the terminal status in the plan task's `## Execution evidence`. **The gate is `Completed`** plus, per dbt activity, the all-green line from `get-dbt-job-evidence.py` given the pipeline run id (the activity passed it as `DBT_OUTPUT_DIR`). The gate reports Failed on a `warn`-severity test result: fix the dbt project, never lower a severity. Static validation is not evidence. Record a failed run but leave the checkbox unchecked; a failure returns to authoring, never to a production fallback or a hand-patched deployed copy.

<sandbox-boundaries>

- **Ephemeral only** (the kind-named `VD_EPHM_FABRIC_*` settings). Never target the domain workspace.
- **Never read or set** `FAB_TOKEN*` / `VD_CREDENTIAL_*` / `AZURE_*`. A `fab` 401 means the user must re-login to Studio; stop.
- **A runner failing on a missing `/lakehouse/default/Files/<slug>/<subdir>` is a DELIVERY failure, never an unreachable-storage one**: deliver that folder (`--source` is the folder, never the repo root). A missing `prod-target/manifest.json` is the same failure for the manifest. No attachment, or one in another workspace, means re-binding in THIS workspace. Never embed the pipeline code in the notebook, never change the committed parameters, never propose a different item kind.
- On a `fab` error, surface the message and request id and stop. For out-of-flow debugging, `./fab-cli-cheatsheet.md`.

</sandbox-boundaries>

## Airflow (`orchestration/` commits a `.ApacheAirflowJob`)

`./airflow-job-sandbox-run.md` replaces steps 1 to 3; step 4 and the boundaries are unchanged.
**The gate is the DAG run reaching terminal success with every task instance green** (read `taskInstances`; `record_run` never fails), with the DAG run id, each task's state and the dbt `run_results.json` evidence in `## Execution evidence`.
