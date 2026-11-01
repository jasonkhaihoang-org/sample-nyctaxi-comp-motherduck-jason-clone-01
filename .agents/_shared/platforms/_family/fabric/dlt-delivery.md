# Deliver the dlt code — Fabric

Puts the committed dlt code where a Fabric notebook reads it, and imports the `<name>_pipeline` notebook into the ephemeral workspace. The full load and the orchestration sandbox run both start here.

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it. Run each step from `/workspace` as one terminal call; the variable step 2 sets persists into later terminal calls.

1. Stage `ingestion/` (`git add ingestion`), because the upload ships tracked files only, then upload it. The uploaded `.dlt/config.toml` gets its `[destination.filesystem]` ids retargeted to these ephemeral coordinates (repo copy untouched).

   ```bash
   bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python \"$SKILL_DIR/../../scripts/platforms/_family/fabric/upload-to-onelake.py\" --source ingestion --workspace-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_WORKSPACE_ID\" --lakehouse-id \"\$VD_EPHM_FABRIC_LAKEHOUSE_ID\" --domain-slug \"\$VD_DOMAIN_SLUG\" --subdir ingestion" \
     && python "$SKILL_DIR/../../scripts/ephemeral_workspace_marker.py" init
   ```

   On a Warehouse Intent pass `--workspace-id` from `VD_EPHM_FABRIC_WAREHOUSE_WORKSPACE_ID`, `--lakehouse-id` from `VD_EPHM_FABRIC_WAREHOUSE_BRIDGE_LAKEHOUSE_ID`, and `--warehouse-id` from `VD_EPHM_FABRIC_WAREHOUSE_ID`: a Warehouse has no `Files/` area, so the code goes to the Ephemeral Paired Lakehouse, and `--warehouse-id` retargets the uploaded `[destination.fabric]`, while a committed staging `[destination.filesystem] bucket_url` moves to that Ephemeral Paired Lakehouse's `Files/staging`. The command runs through `vd-intent-context-run.sh`, which supplies every coordinate to it.

2. Import the `<name>_pipeline` notebook as committed. The import attaches this workspace's code Lakehouse to the copy it imports, which is where the notebook finds `Files/<slug>/ingestion`.

   ```bash
   DLT_ID=$(bash "$SKILL_DIR/../../scripts/platforms/_family/fabric/import-notebook.sh" <name>_pipeline ingestion/<name>_pipeline.Notebook)
   ```
