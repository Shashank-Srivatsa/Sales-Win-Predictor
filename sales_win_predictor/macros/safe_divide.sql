{% macro safe_divide(numerator, denominator) %}
    CASE
        WHEN {{ denominator }} = 0 OR {{ denominator }} IS NULL
        THEN NULL
        ELSE {{ numerator }}::FLOAT / {{ denominator }}::FLOAT
    END
{% endmacro %}
