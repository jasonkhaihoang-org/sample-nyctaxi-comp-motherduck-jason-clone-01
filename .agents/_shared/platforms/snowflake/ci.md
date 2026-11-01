# CI bundle placeholders — snowflake

Read by `install-ci` after `bundle_deploy.py` has written `.workflow/ci-config.yml` and the shared `VD_DOMAIN_SLUG` substitution is done.

## Placeholders

- Replace `VD_DOMAIN_SNOWFLAKE_DATABASE: <database>` with the value of `VD_DOMAIN_SNOWFLAKE_DATABASE`.
- Replace `VD_DOMAIN_SNOWFLAKE_PRIMARY_SCHEMA: <schema>` with `VD_DOMAIN_SNOWFLAKE_PRIMARY_SCHEMA` when it is set and non-empty; otherwise delete that line entirely. Never leave a literal `<schema>` in the committed file.

## Repo-map roles

Read by `onboarding`. The `artifact_paths` roles that differ on this platform; every other CI role is the template's. A folder role ends in `/`.

| Role | Path |
| --- | --- |
| `pipeline` | `ingestion/{name}_pipeline.py` |
