-- fact_opportunities_scored.sql
--
-- PURPOSE: Single table for Power BI that joins every opportunity with its
-- latest ML prediction. Power BI imports this one table instead of joining
-- two separate tables itself — keeping report logic simple.
--
-- GRAIN: one row per opportunity (same as fact_opportunities).
-- Open deals  -> have win_probability, probability_band, shap factors filled.
-- Closed deals -> prediction columns are NULL (we knew the outcome at close time).
--
-- REFRESH: run after every execution of 06_write_predictions.py.

WITH latest_predictions AS (
    -- ML_PREDICTIONS is append-only (one new row per deal per scoring day).
    -- ROW_NUMBER picks only the most recent prediction for each deal,
    -- so we never get duplicate rows in the output.
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY opportunity_id
                ORDER BY scored_at DESC
            ) AS rn
        FROM {{ source('ml', 'ML_PREDICTIONS') }}
    )
    WHERE rn = 1
)

SELECT
    -- ── All columns from the core fact table ─────────────────────────────────
    f.*,

    -- ── ML prediction columns (NULL for closed deals) ────────────────────────
    p.win_probability,
    p.win_predicted,
    p.probability_band,
    p.top_positive_factors,
    p.top_negative_factors,
    p.model_version,
    p.prediction_date,
    p.scored_at     AS last_scored_at

FROM {{ ref('fact_opportunities') }} f
LEFT JOIN latest_predictions p
    ON f.opportunity_id = p.opportunity_id
