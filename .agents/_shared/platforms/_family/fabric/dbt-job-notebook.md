# dbt job notebook — Fabric

`SKILL_DIR` in the commands below is `SKILL_DIR=<this skill's directory>`; substitute it, the runtime does not expand it.

Each dbt job has its own committed `orchestration/<job>.Notebook/`, carrying that job's dbt commands. Its `TridentNotebook` activity — or the Airflow item's `dbt_build` task — invokes it and passes one parameter, `DBT_OUTPUT_DIR`. The same notebook runs unchanged in the Intent's sandbox and in production.

## Generate

```bash
# SKILL_DIR is the invoking skill's directory; the runtime does not expand it.
SKILL_DIR="<this skill's directory>" \
  && cd /workspace \
  && bash "$SKILL_DIR/../../scripts/vd-intent-context-run.sh" "python3 \"$SKILL_DIR/../../scripts/platforms/_family/fabric/materialize-dbt-job-notebook.py\" <job>_dbt --platform <lakehouse|warehouse> --domain-slug \"\$VD_DOMAIN_SLUG\" --out orchestration"
```

Then author the run cell's commands — replace `<selector>` with the job's selection, e.g. `dbt build --select +fct_orders`, and drop `dbt deps` when the project has no `packages.yml` — and leave the install and prerequisites cells as written.

## What it reads and writes

- **Code path:** the attached default Lakehouse, `Files/<slug>/transformation` — the Domain Lakehouse, or on a Warehouse Domain the Ephemeral Paired Lakehouse. CD delivers the project there in production; `upload-to-onelake.py` delivers it in the ephemeral sandbox. The committed item carries no attachment — `import-notebook.sh` binds one on the copy it imports.
- **Profile:** the Intent's own profile when one was delivered, else the project's `transformation/profiles.yml` (below).
- **Defer:** automatic outside production — the prerequisites cell turns it on — so the commands never pass `--defer`.
- **Evidence:** dbt writes its own `target/` (`run_results.json`, `manifest.json`, compiled SQL) and `dbt.log` into `Files/<slug>/runs/<DBT_OUTPUT_DIR>/`, emptied at the start of each run. `run_results.json` is the last results-writing command's, so `dbt run` then `dbt test` grades the tests; prefer one `dbt build`. The first failing command fails the notebook, and so the activity.

## The profile

`transformation/profiles.yml` is committed, and its **`prod` target holds the Domain's fixed coordinates** — never an `env_var()`: a Fabric notebook has none of the agent's environment. Its default target is `prod`.

When authoring orchestration, read the file:

- **No file, or no `prod` target** — tell the user, then create it from `./templates/dbt-profiles-lakehouse.yml` or `./templates/dbt-profiles-warehouse.yml`: `<profile_name>` is the fallback literal in `transformation/dbt_project.yml`'s `profile: "{{ env_var('DBT_PROFILE_NAME', '<fallback>') }}"` (a Domain notebook run does not rely on `DBT_PROFILE_NAME`), or the bare `profile:` value while the project is not yet converted — this is the repository's committed profile, not the one Studio renders — and each `<VD_…>` placeholder is that setting's value.
- **`prod` uses `env_var()` or a placeholder** — ask the user to make it fixed; do not rewrite it.
- **`prod` holds fixed values** — nothing to do.

Git never carries an ephemeral target. The Intent's own profile is `~/fab_notebook_profile/profiles.yml`, which Studio writes at Open with one **`ephemeral_platform`** target holding the Intent's literal coordinates; edit it when an Intent run needs different settings, and delete it to have the next Open write it again. `upload-to-onelake.py` ships it beside the project, and the notebook reads it instead of the project's own whenever it is there — so the same notebook builds into production from the Domain workspace and into the Intent from an ephemeral one.

The two profiles are separate files, so a Spark size in `prod`'s `spark_config` reaches an Intent run only if the Intent profile carries it too; any size but the Starter Pool's Medium nodes starts an on-demand session, 2 to 5 minutes before the first statement.

On a Lakehouse, a model's custom `+schema` holds on `ephemeral_platform` only through the project's `macros/generate_schema_name.sql` override: `dbt-fabricspark` alone honours it only on a target named `prod`.

## Lakehouse and Warehouse

| | `fabric_lakehouse` | `fabric_warehouse` |
| --- | --- | --- |
| Adapter and identity | `dbt-fabricspark` over Livy, `authentication: fabric_notebook` | `dbt-fabric` over TDS, `authentication: notebookutils` |
| Attached Lakehouse | the Domain's own Lakehouse — also the target | the Intent's **Ephemeral Paired Lakehouse**, which carries the Domain Warehouse's name; code only |
| Defer from the ephemeral workspace | unselected `ref()`s read the Domain's four-part relations across workspaces | unselected `ref()`s read `[<domain warehouse>].[schema].[table]`, which resolves to the Ephemeral Paired Lakehouse: it carries the Domain Warehouse's name and each Domain schema as a shortcut. A production schema created after the Ephemeral Paired Lakehouse was last mirrored is not on it, so a `ref()` into it fails `Invalid object name` until the Intent is reopened, which re-mirrors it |
| Run time | 4 to 5 minutes: each dbt command opens its own Spark session | about 1.5 minutes: no Spark session |

## Activity parameter

`DBT_OUTPUT_DIR` is the pipeline run id, as the expression `{"value": {"value": "@pipeline().RunId", "type": "Expression"}, "type": "string"}` — nested exactly so; Fabric fails the run on a flat `{"value": "@…", "type": "Expression"}`. The notebook cannot learn its own run id, so the caller names the folder it will read the evidence from. An Airflow DAG passes its own run id instead (`./airflow-job.md`); a run started by hand keeps `manual`. The notebook takes nothing else (`validate-datapipeline.py` rejects any other parameter).
