# CI bundle placeholders — fabric_warehouse

Read by `install-ci` after `bundle_deploy.py` has written `.workflow/ci-config.yml` and the shared `VD_DOMAIN_SLUG` substitution is done.

## Placeholders

Replace each placeholder with the assigned coordinate of the same name: `VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_ID: <workspace-guid>`, `VD_DOMAIN_FABRIC_WAREHOUSE_WORKSPACE_NAME: <workspace-name>`, `VD_DOMAIN_FABRIC_WAREHOUSE_ID: <warehouse-guid>`, `VD_DOMAIN_FABRIC_WAREHOUSE_NAME: <warehouse-name>` and `VD_DOMAIN_SCHEMA: <schema-name>`. All five are required, the two names included: a three-part TDS name records no workspace, so a deferred relation resolves only by the Warehouse's name. An unset or empty name is an incomplete binding — halt per `install-ci` step 4; never delete the line or keep the placeholder. Also replace `VD_DOMAIN_FABRIC_WAREHOUSE_CODE_LAKEHOUSE_ID: <lakehouse-guid>` with that coordinate: the production deploy delivers the notebooks' code to that Lakehouse. When it is unset, leave the placeholder: the production deploy and the bulk staging of loads both need the Paired Lakehouse, and the placeholder names the gap. Leave the `LLM_*_VAR` block exactly as the template shipped it — static GHA name-indirection keys (ADR 0018), not Domain data.

## Repo-map roles

Read by `onboarding`. The `artifact_paths` roles that differ on this platform; every other CI role is the template's. A folder role ends in `/`.

| Role | Path |
| --- | --- |
| `pipeline` | `ingestion/{name}_pipeline.Notebook/` |
