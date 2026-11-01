{#-
    dbt's --defer rewrites ref() but never source() (https://github.com/dbt-labs/dbt-core/issues/10912).
    This override gives source() the same rule:
        no --defer                      -> stock dbt, a pure passthrough
        --defer, table exists locally  -> the Intent's own relation wins
        --defer, table missing locally -> the deferred workspace + lakehouse
        --defer --favor-state          -> the deferred workspace + lakehouse, always

    The relation's `database` is the Lakehouse, and the Ephemeral Lakehouse carries the Domain's
    name, so `database` cannot tell the two apart. The workspace is carried only by the rendered
    4-part `defer_relation.relation_name` (`workspace`.`lakehouse`.`schema`.identifier) that the
    production manifest gives every deferred node, so it is parsed back out of that.

    A 3-part name means the deferred target set no `workspace_name` or the Lakehouse is not
    schema-enabled; the segment-count assert fails loudly rather than emitting a wrong location.
    `dbt docs generate` bypasses source() overrides (https://github.com/dbt-labs/dbt-core/issues/6308).
    Remove once https://github.com/dbt-labs/dbt-core/issues/10912 lands.
-#}
{% macro source(source_name, table_name) %}

    {% set rel = builtins.source(source_name, table_name) %}

    {% if execute and invocation_args_dict.get('defer') %}

        {#- The identifier is never quoted while database and schema always are, so a 4-part name
            yields exactly 3 quoted segments and a 3-part one 2: the count is the shape check. -#}
        {% set locs = [] %}
        {% for node in graph.nodes.values() %}
            {% set dr = node.get('defer_relation') %}
            {% if dr and dr.get('relation_name') %}
                {% set segs = modules.re.findall('`([^`]*)`', dr['relation_name']) %}
                {% if segs | length != 3 %}
                    {% do exceptions.raise_compiler_error(
                        'source_defer: expected a 4-part defer_relation '
                        ~ '(`workspace`.`lakehouse`.`schema`.identifier), got '
                        ~ (segs | length) ~ ' quoted segments in: '
                        ~ dr['relation_name']
                        ~ ' — the deferred target must set workspace_name against a '
                        ~ 'schema-enabled lakehouse.') %}
                {% endif %}
                {% do locs.append((segs[0], segs[1])) %}
            {% endif %}
        {% endfor %}

        {% if locs %}
            {% set counts = {} %}
            {% for l in locs %}{% do counts.update({l: counts.get(l, 0) + 1}) %}{% endfor %}
            {% set deferred = (counts | dictsort(by='value') | last)[0] %}

            {% if invocation_args_dict.get('favor_state')
                  or not adapter.get_relation(rel.database, rel.schema, rel.identifier) %}
                {% set rel = rel.replace_path(database=deferred[1]).incorporate(workspace=deferred[0]) %}
            {% endif %}
        {% endif %}

    {% endif %}

    {% do return(rel) %}

{% endmacro %}
