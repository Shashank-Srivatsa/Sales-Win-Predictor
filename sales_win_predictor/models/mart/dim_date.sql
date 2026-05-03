-- Date spine from 2015-01-01 to 2025-12-31
WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-01-01' as date)",
        end_date="cast('2026-01-01' as date)"
    ) }}
)

SELECT
    -- Surrogate key: integer YYYYMMDD — readable and joins cheaply as INT
    TO_NUMBER(TO_CHAR(date_day, 'YYYYMMDD'))                        AS date_sk,

    -- Natural key
    date_day,

    -- Calendar attributes
    EXTRACT(YEAR   FROM date_day)::INT                              AS year,
    EXTRACT(QUARTER FROM date_day)::INT                             AS quarter,
    EXTRACT(MONTH  FROM date_day)::INT                              AS month,
    TO_CHAR(date_day, 'MMMM')                                      AS month_name,
    EXTRACT(WEEK   FROM date_day)::INT                              AS week_of_year,
    DAYOFWEEK(date_day)                                             AS day_of_week,
    CASE WHEN DAYOFWEEK(date_day) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,

    -- Last 14 days of March, June, September, December
    CASE
        WHEN EXTRACT(MONTH FROM date_day) IN (3, 6, 9, 12)
         AND date_day >= LAST_DAY(date_day) - INTERVAL '13 days'
        THEN TRUE ELSE FALSE
    END                                                             AS is_fiscal_quarter_end,

    CASE WHEN date_day = LAST_DAY(date_day) THEN TRUE ELSE FALSE END AS is_month_end,

    EXTRACT(YEAR FROM date_day)::INT                                AS fiscal_year,
    'FY' || EXTRACT(YEAR FROM date_day)::VARCHAR
        || '-Q' || EXTRACT(QUARTER FROM date_day)::VARCHAR          AS fiscal_quarter_label
FROM date_spine
