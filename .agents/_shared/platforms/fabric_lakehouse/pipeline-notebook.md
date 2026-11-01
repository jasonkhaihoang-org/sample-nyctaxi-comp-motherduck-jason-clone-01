# The dlt pipeline notebook

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

On `fabric_lakehouse` the pipeline IS the notebook: `ingestion/<name>_pipeline.Notebook/` carries the load's own code. It runs in the sandbox as plain Python and on Fabric as the notebook a `TridentNotebook` activity invokes. An `.ApacheAirflowJob` does not invoke it: a DAG task triggers the dlt runner notebook instead (`../_family/fabric/orchestration-authoring.md`).

## Generate

```bash
# SKILL_DIR is the invoking skill's directory; the runtime does not expand it.
SKILL_DIR="<this skill's directory>" \
  && cd /workspace \
  && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python3 \"$SKILL_DIR/../../scripts/platforms/_family/fabric/materialize-dlt-pipeline-notebook.py\" <name> --out ingestion --domain-slug \"\$VD_DOMAIN_SLUG\" --platform \"\$VD_DOMAIN_DATA_PLATFORM\""
```

`vd-intent-context-run.sh` supplies `VD_DOMAIN_SLUG` and `VD_DOMAIN_DATA_PLATFORM` (which picks the template) to the command.

It writes `notebook-content.py` from the template and mints `.platform` once. Re-running keeps both. Never re-mint the `logicalId`: the activity references the item by it.

Then author the last cell — connector import, `dlt.pipeline(...)`, hints, `finalize()` — as `generating-dlt-pipeline` directs.

## Run

```bash
# SKILL_DIR is the invoking skill's directory; the runtime does not expand it.
SKILL_DIR="<this skill's directory>" \
  && cd /workspace/ingestion \
  && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" 'DEV_MODE=true DLT_INGEST_LIMIT=1 python <name>_pipeline.Notebook/notebook-content.py'
```

`DEV_MODE=true DLT_INGEST_LIMIT=1` makes this the safety run (`../../../skills/generating-dlt-pipeline/SKILL.md`).
Always run through `vd-intent-context-run.sh`: the `vibedata.dlt.*` bootstrap gets its destination and credential from the Intent's settings that the runner supplies.

## Editing the generated cells

Keep the cell order: **parameters → mount → install → `setup_environment()` → the load**. The install cell has to follow the mount, because the shell inherits the working directory the mount sets and resolves `requirements.txt` from the delivery.

In the install cell, use `pip`, not `python3 -m pip` — on the Fabric kernel `python3` is `/usr/bin/python3` and carries no pip.

Keep `%%sh` as its cell's first line, and use no line magic anywhere. A cell magic is stored as `# MAGIC` comments, which is what makes the sandbox skip the install and keep the distribution its image provides. A line magic is stored raw and stops the file being Python.

Put no runtime unit in `requirements.txt`. The sandbox installs that file too, and the notebook unit landing there would replace the Studio unit.

## Delivery

OneLake carries `.dlt/config.toml`, `requirements.txt` and `sources/` — everything the pipelines share, and no pipeline code. `upload-to-onelake.py` excludes `.Notebook` directories; the notebook reaches the workspace as a Fabric item through `import-notebook.sh`, which attaches the Lakehouse.

A notebook's own `Resources/builtin/` cannot carry the shared files: the definition API accepts a `builtin/` part, reports success, and discards it. A Fabric Environment is not available for Python notebooks.
