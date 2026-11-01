{#- dbt-fabric has no schema macro of its own, so dbt's built-in would build `<target schema>_<custom>` (`dbo_raw`). -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
