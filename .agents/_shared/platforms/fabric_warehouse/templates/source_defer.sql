{#- Copied verbatim to `macros/source_defer.sql`. A project macro named `source` replaces dbt's built-in for every
    `{{ source() }}` call, so models and plain `dbt` invocations stay as they are. The sources YAML names the Domain's
    database, and the Intent's Ephemeral Paired Lakehouse carries that exact name with each Domain schema mirrored onto it, so
    `builtins.source` already renders the Domain table through the Ephemeral Paired Lakehouse and records the dependency. In a sandbox
    (the target database is not the Domain's) one metadata lookup per source at compile reads the sandbox's own table
    when it exists; otherwise one schemata query checks the Ephemeral Paired Lakehouse carries the Domain schema, and a schema created
    after the Ephemeral Paired Lakehouse was last mirrored fails here with a named error instead of an `Invalid object name` later. A missing table
    in a mirrored schema is left to fail where it is read. Every lookup is guarded by `execute`, so `dbt parse` never
    queries the database, and in prod and CI the target is the Domain's database, so none runs. -#}
{% macro source(source_name, table_name) -%}
    {%- set domain = builtins.source(source_name, table_name) -%}
    {%- if not execute or (target.database | lower) == (domain.database | lower) -%}
        {%- do return(domain) -%}
    {%- endif -%}
    {%- set own = adapter.get_relation(database=target.database, schema=domain.schema, identifier=domain.identifier) -%}
    {%- if own is not none -%}
        {%- do return(own) -%}
    {%- endif -%}
    {%- if run_query(source_defer_schemata_sql(domain.database, domain.schema)) | length == 0 -%}
        {%- do exceptions.raise_compiler_error(
            "source('" ~ source_name ~ "', '" ~ table_name ~ "'): the Domain schema " ~ domain.schema
            ~ " is not on the Ephemeral Paired Lakehouse " ~ domain.database ~ ". The schema was created after the Ephemeral Paired Lakehouse was last mirrored,"
            ~ " and the Ephemeral Paired Lakehouse is re-mirrored each time the Intent is opened, so reopen the Intent before this source can be"
            ~ " read (ADR-0035).") -%}
    {%- endif -%}
    {%- do return(domain) -%}
{%- endmacro %}

{#- One row when the Ephemeral Paired Lakehouse carries the schema. `adapter.quote` brackets the name and doubles a `]`. -#}
{% macro source_defer_schemata_sql(bridge, schema) -%}
    {{ return(adapter.dispatch('source_defer_schemata_sql')(bridge, schema)) }}
{%- endmacro %}

{% macro default__source_defer_schemata_sql(bridge, schema) -%}
    {{ return("select 1 from " ~ adapter.quote(bridge) ~ ".INFORMATION_SCHEMA.SCHEMATA where SCHEMA_NAME = '" ~ (schema | replace("'", "''")) ~ "'") }}
{%- endmacro %}
