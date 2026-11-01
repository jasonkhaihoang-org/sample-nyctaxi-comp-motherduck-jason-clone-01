# dlt full load — Fabric Lakehouse

The full load runs the `<name>_pipeline` notebook in the Intent's ephemeral workspace through a temporary one-activity pipeline, `temp_<name>_full_load`, that is never committed and is deleted after its run: a pipeline run reports the notebook's error, a bare notebook run does not.
Nothing sets `DLT_INGEST_LIMIT` there, so it loads everything.

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

1. Deliver the dlt code per `../_family/fabric/dlt-delivery.md`. It sets `DLT_ID`.

2. Prepare the temporary pipeline from `./templates/full-load.DataPipeline/` into `/tmp`, mapping its placeholder notebook id to `DLT_ID`:

   ```bash
   EPHM=$(mktemp -d /tmp/full-load-XXXX) && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$SKILL_DIR/../../scripts/platforms/_family/fabric/prepare-ephemeral-import.py\" \"$SKILL_DIR/../../_shared/platforms/fabric_lakehouse/templates/full-load.DataPipeline\" --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --map \"11111111-1111-1111-1111-111111111111=$DLT_ID\" --out \"$EPHM\""
   ```

3. Import and run it as `../_family/fabric/orchestration-sandbox-run.md` step 4 does, with `FAB` set as that page sets it, `NAME=temp_<name>_full_load`, `EPHM` from step 2, and `temp_<name>_full_load` for that step's `<name>`. A failed run's status carries the notebook's error.

4. Delete the prepared copy and the temporary pipeline whatever the result, once nothing of the run can still be going: its status is terminal and read, with its error on a failure, or the import never created a run. Never while a run is still going: a local wait ending does not end the remote run.

   ```bash
   rm -rf "$EPHM" && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" 'fab rm "$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_NAME.Workspace/temp_<name>_full_load.DataPipeline" -f --hard'
   ```

5. The evidence is the run reaching `Completed`, then `audit_runs` in the loaded dataset, read with `lakehouse_query`, showing this run with `first_run` true and a nonzero `total_rows_extracted`. A `Completed` run that extracted nothing restored an earlier cursor and did not load. On a `fab` error, report the message and request id and stop.

6. Return to `../../../skills/generating-dlt-pipeline/SKILL.md` for the Tier-1 gate (`run_bronze_tier1_tests.py --dataset <schema> --audit`, from `/workspace/ingestion`), then re-render the bronze preview from this load. `assert_destination.py` does not apply: it reads the sandbox's own run.
