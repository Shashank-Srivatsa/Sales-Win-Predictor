{% macro fiscal_quarter_end(date_column) %}
    CASE
        WHEN EXTRACT(MONTH FROM {{ date_column }}) IN (3, 6, 9, 12)
         AND {{ date_column }} >= LAST_DAY({{ date_column }}) - INTERVAL '13 days'
        THEN 1
        ELSE 0
    END
{% endmacro %}
