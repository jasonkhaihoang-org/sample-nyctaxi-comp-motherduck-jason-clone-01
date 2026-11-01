{#- dbt-fabricspark's own macro honours a custom schema only on a target named `prod`, and
    resolves `generate_schema_name_for_env` to dbt's built-in, so only this override keeps
    a node's schema identical across targets, for defer: https://github.com/dbt-labs/dbt/issues/16330 -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set schemas_enabled = adapter.is_lakehouse_schemas_enabled() or adapter.is_local_mode()
        or (target.schema is defined and target.lakehouse is defined and target.schema != target.lakehouse) -%}
    {%- if not schemas_enabled -%}
        {{ target.lakehouse }}
    {%- elif custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
