{#- Replaces dbt's built-in `source()`: in a sandbox (VD_EPHM_SCHEMA_PREFIX set) a source reads the Intent's prefixed
    schema in the target database when it holds the table, else the Domain's relation the sources YAML names. The lookup is
    guarded by `execute`, so `dbt parse` never queries the warehouse, and with no prefix (prod and CI) none runs. -#}
{% macro source(source_name, table_name) -%}
    {%- set domain = builtins.source(source_name, table_name) -%}
    {%- set prefix = env_var('VD_EPHM_SCHEMA_PREFIX', '') -%}
    {%- if prefix and execute -%}
        {%- set loaded = adapter.get_relation(database=target.database, schema=prefix ~ domain.schema, identifier=domain.identifier) -%}
        {%- if loaded is not none -%}
            {%- do return(loaded) -%}
        {%- endif -%}
    {%- endif -%}
    {%- do return(domain) -%}
{%- endmacro %}
