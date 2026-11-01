# Orchestration authoring — Fabric

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

The Fabric authoring steps of `generating-orchestration`, shared by both Fabric platforms: `orchestration/<Name>.DataPipeline/` or `orchestration/<Name>.ApacheAirflowJob/`, plus the execution item each workload invokes.
A committed `.ApacheAirflowJob` replaces steps 3-4 with `./airflow-job.md`.
A `.DataPipeline` committed alongside a `.ApacheAirflowJob` is a defect: halt.

Every execution item is materialized from the plugin's template, never hand-authored and never round-tripped through Fabric (an export commits ephemeral ids).
The committed item carries **no environment binding** (no ids, no workspace, no attachment); the materializer prints the logicalId the activity references and touches nothing in Fabric.

1. **A `.DataPipeline` target has no dlt runner on either platform.** The pipeline notebook at `ingestion/<name>_pipeline.Notebook/` carries the load's own code and is the item the activity invokes, so skip this step entirely and use that item's `.platform` logicalId in step 3.

   An `.ApacheAirflowJob` target still triggers a dlt workload through a runner, because a DAG task names a deployed notebook rather than committing an activity against it. There, reuse the committed `orchestration/<runner>.Notebook/` when one is already there; otherwise materialize it, passing the Domain's own Data Platform:

   ```bash
   SKILL_DIR=<this skill's directory> && python3 "$SKILL_DIR/../../scripts/platforms/_family/fabric/materialize-runner.py" dlt_notebook_runner --engine dlt --platform <lakehouse|warehouse> --out orchestration
   ```

   What a dlt runner is, its two parameters, and every Lakehouse/Warehouse difference: `./dlt-runner-notebook.md`.

2. For each **dbt** workload, the execution item is that job's own notebook, `orchestration/<job>_dbt.Notebook/`, carrying the job's dbt commands. Reuse the committed one on `modify`; otherwise materialize it and author its commands as `./dbt-job-notebook.md` § "Generate" says. Then check `transformation/profiles.yml` against `./dbt-job-notebook.md` § "The profile". Done means the job notebook and a fixed `prod` are committed and the notebook's logicalId is in hand for step 3.

3. Author `orchestration/<Name>.DataPipeline/pipeline-content.json`; a dbt-only row still gets a one-activity pipeline, and each cadence gets its own pipeline. Preserve `.platform` byte-for-byte on `modify`, replace it on `recreate`, and write one native activity per workload in dependency order with `Succeeded` dependencies and design-approved retry/timeout policy.

   - **dlt workload → `TridentNotebook` activity**: `typeProperties.notebookId` = the invoked item's `.platform` `logicalId` — the pipeline notebook in `ingestion/` on both Fabric platforms — and `typeProperties.workspaceId` = the all-zeros GUID, both as FLAT keys — the shape Fabric Git export produces and Fabric deploy auto-binds. Never a nested `notebook` / `notebookReference` object with a `referenceName`: that is the Synapse shape, and Fabric refuses the whole document with `'NotebookId' cannot be null`. `typeProperties.parameters` carries exactly the invoked item's parameters, each as `{"value": …, "type": "string"}`, and every value is the **literal Domain coordinate written out** — the string `VD_DOMAIN_SLUG` holds, never the variable's name. Fabric passes a notebook parameter through verbatim, so a committed variable reference reaches the notebook as that literal text and the run dies on it. So `DOMAIN_SLUG` = the value of `VD_DOMAIN_SLUG`, and that is the whole parameter list: a pipeline notebook is one notebook per pipeline, so it needs nothing naming which pipeline to run.
   - **dbt workload → `TridentNotebook` activity** invoking that job's notebook from step 2, in the same flat shape. Its one parameter is `DBT_OUTPUT_DIR`, the pipeline run id, in the nested expression shape `./dbt-job-notebook.md` § "Activity parameter" gives.

     The dlt parameters are Domain coordinates, identical in every workspace, so committing them binds nothing ephemeral. Everything else an item needs is stated elsewhere — its workspace in the runtime, its code in the artifact or through the attachment, a dlt destination in the committed `.dlt/config.toml`, a dbt target in the committed `profiles.yml` — so the parameters are exactly the ones listed: no workspace, Lakehouse or Warehouse id or name, and no correlation parameter. `validate-datapipeline.py` enforces the shape and rejects a `$`- or `@`-prefixed value.

      Start from this template: one activity per workload, in dependency order. Fill every `<…>` slot. A dbt-only row keeps `build_<job>` alone with `"dependsOn": []`, and a second workload of either kind repeats its activity.

   <template>
   `orchestration/<Name>.DataPipeline/pipeline-content.json`

   ```json
   {
     "properties": {
       "activities": [
         {
           "name": "load_<name>",
           "type": "TridentNotebook",
           "dependsOn": [],
           "policy": {"timeout": "<design timeout, d.hh:mm:ss>", "retry": "<design retry count>", "retryIntervalInSeconds": 30, "secureOutput": false, "secureInput": false},
           "typeProperties": {
             "notebookId": "<logicalId from ingestion/<name>_pipeline.Notebook/.platform>",
             "workspaceId": "00000000-0000-0000-0000-000000000000",
             "parameters": {
               "DOMAIN_SLUG": {"value": "<the string VD_DOMAIN_SLUG holds>", "type": "string"}
             }
           }
         },
         {
           "name": "build_<job>",
           "type": "TridentNotebook",
           "dependsOn": [{"activity": "load_<name>", "dependencyConditions": ["Succeeded"]}],
           "policy": {"timeout": "<design timeout, d.hh:mm:ss>", "retry": "<design retry count>", "retryIntervalInSeconds": 30, "secureOutput": false, "secureInput": false},
           "typeProperties": {
             "notebookId": "<logicalId from orchestration/<job>_dbt.Notebook/.platform>",
             "workspaceId": "00000000-0000-0000-0000-000000000000",
             "parameters": {
               "DBT_OUTPUT_DIR": {"value": {"value": "@pipeline().RunId", "type": "Expression"}, "type": "string"}
             }
           }
         }
       ]
     }
   }
   ```

   `orchestration/<Name>.DataPipeline/.platform`

   ```json
   {
     "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
     "metadata": {"type": "DataPipeline", "displayName": "<Name>"},
     "config": {"version": "2.0", "logicalId": "<logicalId: preserved on modify, new uuid4 on create or recreate>"}
   }
   ```

   </template>

   For `.platform`, preserve the `logicalId` on `modify` and write a fresh uuid4 that no other committed item uses on `create` and `recreate`, never reusing one; deploy rejects a missing `.platform` or a duplicate logicalId.

   Mint a `logicalId` only for a brand-new item, and commit only portable logicalIds — never a raw workspace object or connection ID.

4. When Schedule is not `none`, author the pipeline's `.schedules` under `./schedule-authoring.md`. Never activate it; ephemeral imports carry no cadence.

5. Run the target's validators from `$SKILL_DIR/../../scripts/platforms/_family/fabric/`, each `--repo-root .`: `validate-datapipeline.py orchestration/<Name>.DataPipeline`, or `validate-airflow-dag.py orchestration/<Name>.ApacheAirflowJob` on the Airflow target. Fix findings and re-run until exit 0. On `modify`, also run `git diff HEAD -- orchestration/<Name>.<Kind>/.platform` and halt on any `logicalId` change.
