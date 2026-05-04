WITH fact AS (
    SELECT * FROM {{ ref('fact_opportunities') }}
),

-- created_date needed for created_month (fact stores only the integer date_sk)
opp_meta AS (
    SELECT opportunity_id, created_date
    FROM {{ ref('stg_crm_opportunities') }}
),

-- account_tier + client average deal value (from dim_account → int_client_deal_history)
dim_acct AS (
    SELECT account_sk, account_tier, avg_deal_value AS client_avg_deal_value
    FROM {{ ref('dim_account') }}
),

-- Division median time-to-close from closed deals only (for velocity score)
division_medians AS (
    SELECT
        division,
        MEDIAN(total_days_in_funnel)                                  AS median_days_to_close
    FROM fact
    WHERE is_won IS NOT NULL AND total_days_in_funnel > 0
    GROUP BY division
)

SELECT
    -- ── Identity & ML split ──────────────────────────────────────────────────
    f.opportunity_id,
    f.opportunity_sk,
    f.fiscal_year,
    f.fiscal_quarter,
    CASE
        WHEN f.is_won IS NOT NULL AND f.fiscal_year <= 2022 THEN 'train'
        WHEN f.is_won IS NOT NULL AND f.fiscal_year >= 2023 THEN 'test'
        WHEN f.is_open = 1                                   THEN 'score'
    END                                                               AS ml_split,

    -- ── Target ───────────────────────────────────────────────────────────────
    f.is_won                                                          AS target_is_won,

    -- ── [A] Deal Value (5 features) ──────────────────────────────────────────
    LN(GREATEST(COALESCE(f.amount, 0), 0) + 1)                        AS deal_value_log,
    f.amount                                                          AS deal_value_raw,
    -- Source stores discount as 0-100 percentage; normalize to 0-1 fraction for XGBoost
    f.discount_pct / 100.0                                            AS discount_pct,
    CASE
        WHEN COALESCE(f.discount_pct, 0) = 0   THEN 0   -- no discount
        WHEN f.discount_pct <= 5               THEN 1   -- low  (≤5%)
        WHEN f.discount_pct <= 15              THEN 2   -- medium (≤15%)
        WHEN f.discount_pct <= 25              THEN 3   -- high (≤25%)
        ELSE 4                                           -- very high (>25%)
    END                                                               AS discount_risk_score,
    {{ safe_divide('f.amount', 'NULLIF(da.client_avg_deal_value, 0)') }}
                                                                      AS deal_size_relative_to_client_avg,

    -- ── [B] Deal Categorical (4 features) ────────────────────────────────────
    CASE f.deal_type
        WHEN 'New'        THEN 0
        WHEN 'Renewal'    THEN 1
        WHEN 'Upsell'     THEN 2
        WHEN 'Cross-sell' THEN 3
        ELSE -1
    END                                                               AS deal_type_encoded,
    CASE f.division
        WHEN 'TalentEdge'     THEN 0
        WHEN 'CreativeMotion' THEN 1
        WHEN 'PulseMedia'     THEN 2
        WHEN 'BrandVault'     THEN 3
        ELSE -1
    END                                                               AS division_encoded,
    CASE f.region
        WHEN 'NA'   THEN 0
        WHEN 'EU'   THEN 1
        WHEN 'IN'   THEN 2
        WHEN 'APAC' THEN 3
        WHEN 'AU'   THEN 4
        ELSE -1
    END                                                               AS region_encoded,
    f.is_renewal,

    -- ── [C] Deal Timing (5 features) ─────────────────────────────────────────
    f.total_days_in_funnel,
    f.days_in_negotiation_stage,
    f.days_in_opportunity_stage,
    EXTRACT(MONTH FROM om.created_date)::INT                          AS created_month,
    f.is_fiscal_quarter_end_period,

    -- ── [D] Deal Complexity (4 features) ─────────────────────────────────────
    f.line_item_count,
    f.deal_complexity_score,
    f.has_usage_rights,
    f.has_minimum_guarantee,

    -- ── [E] Velocity (1 feature) ─────────────────────────────────────────────
    -- >1 means deal is faster than median (positive signal), <1 means slower
    {{ safe_divide('dm.median_days_to_close', 'NULLIF(f.total_days_in_funnel, 0)') }}
                                                                      AS deal_velocity_score,

    -- ── [F] Agent (5 features) ───────────────────────────────────────────────
    f.agent_trailing_12m_win_rate,
    f.agent_seniority_level,
    f.agent_current_open_deals,
    f.agent_win_rate_this_division,
    f.is_vertical_specialist,

    -- ── [G] Client (4 features) ──────────────────────────────────────────────
    f.client_win_rate,
    f.client_is_new,
    f.client_days_since_last_deal,
    COALESCE(da.account_tier, {{ var('default_account_tier') }})      AS account_tier,

    -- ── [H] Engagement (4 features) ──────────────────────────────────────────
    f.total_activities,
    f.days_since_last_activity,
    f.engagement_score,
    f.positive_activity_ratio,

    -- ── [I] Negotiation Risk (2 features) ────────────────────────────────────
    f.stage_regression_count,
    f.contract_revision_count,

    CURRENT_TIMESTAMP                                                  AS _loaded_at

FROM fact f
LEFT JOIN opp_meta om       ON f.opportunity_id = om.opportunity_id
LEFT JOIN dim_acct da       ON f.account_sk = da.account_sk
LEFT JOIN division_medians dm ON f.division = dm.division
