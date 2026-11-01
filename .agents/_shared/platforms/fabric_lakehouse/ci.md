# CI bundle placeholders — fabric_lakehouse

Read by `install-ci` after `bundle_deploy.py` has written `.workflow/ci-config.yml` and the shared `VD_DOMAIN_SLUG` substitution is done.

## Placeholders

Replace `VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_ID: <guid>` and `VD_DOMAIN_FABRIC_LAKEHOUSE_ID: <guid>` with `VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_ID`/`VD_DOMAIN_FABRIC_LAKEHOUSE_ID`. Replace `VD_DOMAIN_SCHEMA: <string>` with `VD_DOMAIN_SCHEMA`; it is required, because the production-manifest publish records it as the schema deferred reads resolve to. For the two optional `<string>` name lines (`..._WORKSPACE_NAME`, `..._NAME`): substitute the real value when `VD_DOMAIN_FABRIC_LAKEHOUSE_WORKSPACE_NAME`/`VD_DOMAIN_FABRIC_LAKEHOUSE_NAME` is set and non-empty, otherwise delete that line entirely — never leave a literal `<string>` in the committed file. Leave the `AZURE_TENANT_ID_VAR`/`AZURE_CLIENT_ID_VAR`/`FABRIC_CAPACITY_ID_VAR`/`LLM_*_VAR`/`VD_DOMAIN_PROD_MANIFEST_SOURCE` block exactly as the template shipped it — those are static GHA name-indirection keys (ADR 0018), not Domain data, and were already correct.

## Repo-map roles

Read by `onboarding`. The `artifact_paths` roles that differ on this platform; every other CI role is the template's. A folder role ends in `/`.

| Role | Path |
| --- | --- |
| `pipeline` | `ingestion/{name}_pipeline.Notebook/` |
