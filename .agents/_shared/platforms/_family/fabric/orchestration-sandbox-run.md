# Orchestration sandbox run — worked example

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

Steps 1 to 3 of `./orchestration-running.md`, as one example: skip the legs a pipeline does not have, and never activate a schedule.

The commands show a `fabric_lakehouse` Intent's coordinates. On a `fabric_warehouse` Intent make two different substitutions:

- every `--workspace-id` is `VD_EPHM_FABRIC_WAREHOUSE_WORKSPACE_ID` (the shell scripts resolve the `.Workspace` name themselves);
- `upload-to-onelake.py --lakehouse-id` is the Ephemeral Paired Lakehouse `VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID` (a Warehouse has no `Files/` area), and `VD_EPHM_FABRIC_WAREHOUSE_ID` goes only to `--warehouse-id`, which retargets the uploaded `[destination.fabric]` (a committed staging `bucket_url` moves to the Ephemeral Paired Lakehouse's `Files/staging` too); the script refuses a Warehouse config without it.

Each step is one command; variables persist into later terminal calls but not into `start_async_bash`.
If a step fails part-way, re-run it rather than continuing, and re-run the setup step if a later one reports a path starting at `/`.
Every coordinate reaches the command through `vd-intent-context-run.sh`.

```bash
FAB="$SKILL_DIR/../../scripts/platforms/_family/fabric" && NAME=nightly_orders && DBT_JOB=nightly_orders_dbt
```

**1. dlt — deliver the code and import the `<name>_pipeline` notebook** per `./dlt-delivery.md`. Its import sets `DLT_ID`, which step 3 maps.

**2. dbt — deliver the project, the Intent's profile, and the defer state.** The upload ships the Intent's `~/fab_notebook_profile/profiles.yml` beside the project (`./dbt-job-notebook.md` § "The profile"). Pass `--prod-manifest` only when `/data/cache/prod-target/manifest.json` exists; without it the notebook builds without defer.

<!-- not-a-runnable-fence: one line per defer state; run the one that matches /data/cache/prod-target -->
```bash
# /data/cache/prod-target/manifest.json exists
bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$FAB/upload-to-onelake.py\" --source transformation --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --lakehouse-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_ID\" --domain-slug \"\$VD_DOMAIN_SLUG\" --subdir transformation --prod-manifest /data/cache/prod-target/manifest.json"
# it does not
bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$FAB/upload-to-onelake.py\" --source transformation --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --lakehouse-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_ID\" --domain-slug \"\$VD_DOMAIN_SLUG\" --subdir transformation"
```

**2b. dbt — import each committed dbt job notebook as-is.** The import attaches the ephemeral Lakehouse, which is where the notebook reads the project.

```bash
DBT_ID=$(bash "$FAB/import-notebook.sh" "$DBT_JOB" "orchestration/$DBT_JOB.Notebook")
```

**3. Remap the committed portable references to the ephemeral ids** (repo copy untouched). One `--map` per imported notebook; drop the ones this pipeline does not invoke.

```bash
DLT_LOGICAL=$(python3 -c "import json;print(json.load(open('ingestion/<name>_pipeline.Notebook/.platform'))['config']['logicalId'])") \
  && DBT_LOGICAL=$(python3 -c "import json;print(json.load(open('orchestration/${DBT_JOB}.Notebook/.platform'))['config']['logicalId'])") \
  && EPHM=$(mktemp -d "/tmp/ephm-$NAME-XXXX") \
  && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$FAB/prepare-ephemeral-import.py\" \"orchestration/${NAME}.DataPipeline\" --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --map \"$DLT_LOGICAL=$DLT_ID\" --map \"$DBT_LOGICAL=$DBT_ID\" --out \"$EPHM\""
```

**4. Deploy, then run on demand — in `start_async_bash`, not a plain terminal call.** `run-item.sh` blocks for the whole run and a terminal call is cut off long before that.

```bash
bash "$FAB/import-pipeline.sh" "$NAME" "$EPHM"
```

Then launch `bash "$SKILL_DIR/../../scripts/platforms/_family/fabric/run-item.sh" "<name>" DataPipeline` with `start_async_bash` and `timeout_seconds: 1800`, with `$SKILL_DIR` and `<name>` (the `<name>.DataPipeline` folder name) substituted, and wait with `wait_for_async_bash` and `wait_timeout_seconds: 300`.
The output carries `Job instance '<run id>' created`; if the local command ends first, read that run with `fab job run-status "<ws>.Workspace/<Name>.DataPipeline" --id <run-id>`.
One run per change: concurrent runs replace the same tables.

**5. Read the dbt evidence for the plan** — the gate is `Completed` plus this all-green line.

```bash
bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$FAB/get-dbt-job-evidence.py\" --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --lakehouse-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_ID\" --domain-slug \"\$VD_DOMAIN_SLUG\" --pipeline-instance-id \"<the run id from run-item.sh's output>\""
```

The line reports Failed on a `warn`-severity test result: fix the dbt project, never weaken a test to `warn`.
