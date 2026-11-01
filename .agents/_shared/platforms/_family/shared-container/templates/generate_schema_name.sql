{#- dbt's default joins target.schema and a custom schema (`<target>_<custom>`), and neither shared-container
    adapter ships its own schema macro, so this one resolves every model, seed and snapshot: the logical schema, behind the
    Studio-sent VD_EPHM_SCHEMA_PREFIX in a sandbox (empty in prod and CI). A sandbox target schema Studio already named with
    the prefix (at times shortened with a digest) is used unchanged. Every other node keeps dbt's default, which starts with
    the target schema: dbt gives each data test `dbt_test__audit`, which the logical-name rule would refuse. It stops on a
    malformed prefix or schema name, or a name over 255 characters, the same rules as dlt's physical_schema() in vibedata-dlt-core. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if node is not none and node.resource_type not in ['model', 'seed', 'snapshot'] -%}
        {{ default__generate_schema_name(custom_schema_name, node) }}
    {%- else -%}
    {%- set prefix = env_var('VD_EPHM_SCHEMA_PREFIX', '') -%}
    {%- if prefix and not modules.re.fullmatch('[a-z0-9]+(_{1,2}[a-z0-9]+)*__', prefix) -%}
        {{ exceptions.raise_compiler_error("VD_EPHM_SCHEMA_PREFIX '" ~ prefix ~ "' must be lowercase segments joined by one or two underscores and end in '__'") }}
    {%- endif -%}
    {%- if custom_schema_name is not none and not modules.re.fullmatch('[a-z0-9]+(_[a-z0-9]+)*', custom_schema_name) -%}
        {{ exceptions.raise_compiler_error("schema '" ~ custom_schema_name ~ "' must be lowercase letters, digits and single inner underscores (no leading, trailing or double underscore, no whitespace)") }}
    {%- endif -%}
    {%- set logical = target.schema if custom_schema_name is none else custom_schema_name -%}
    {%- set physical = logical if custom_schema_name is none and prefix and logical.startswith(prefix) else prefix ~ logical -%}
    {%- if physical | length > 255 -%}
        {{ exceptions.raise_compiler_error("schema '" ~ physical ~ "' is longer than 255 characters; shorten the schema name") }}
    {%- endif -%}
    {{ physical }}
    {%- endif -%}
{%- endmacro %}
