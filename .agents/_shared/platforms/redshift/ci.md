# CI bundle placeholders — redshift

## Placeholders

- Required, from the assigned coordinate of the same name: `VD_DOMAIN_REDSHIFT_HOST: <host>`, `VD_DOMAIN_REDSHIFT_PORT: <port>`, `VD_DOMAIN_REDSHIFT_DATABASE: <database>`, `VD_DOMAIN_SCHEMA: <schema-name>`.
- Exactly one of `VD_DOMAIN_REDSHIFT_CLUSTER_IDENTIFIER: <cluster-identifier>` or `VD_DOMAIN_REDSHIFT_WORKGROUP_NAME: <workgroup-name>` is assigned: fill it and delete the other line, the only deletion allowed.
- Neither assigned, or any required value empty, is an incomplete binding: halt per `install-ci`; never keep a placeholder.

## Repo-map roles

Read by `onboarding`. The `artifact_paths` roles that differ on this platform; every other CI role is the template's. A folder role ends in `/`.

| Role | Path |
| --- | --- |
| `pipeline` | `ingestion/{name}_pipeline.py` |
