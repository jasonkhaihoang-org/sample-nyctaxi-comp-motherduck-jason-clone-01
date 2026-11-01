# CI bundle placeholders — motherduck

## Placeholders

- Replace `VD_DOMAIN_MOTHERDUCK_DATABASE: prd` with the value of `VD_DOMAIN_MOTHERDUCK_DATABASE`; never trust the template's literal.
- Leave `MOTHERDUCK_TOKEN_VAR`, `LLM_*_VAR` and `VD_DOMAIN_PROD_MANIFEST_SOURCE` untouched.

## Repo-map roles

Read by `onboarding`. The `artifact_paths` roles that differ on this platform; every other CI role is the template's. A folder role ends in `/`.

| Role | Path |
| --- | --- |
| `pipeline` | `ingestion/{name}_pipeline.py` |
| `pipeline_flight` | `ingestion/{name}_pipeline.Flight/` |
