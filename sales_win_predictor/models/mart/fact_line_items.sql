WITH line_items AS (
    SELECT * FROM {{ ref('stg_crm_line_items') }}
),

-- Pull only the keys + context measures we need from fact_opportunities
opportunities AS (
    SELECT
        opportunity_sk,
        opportunity_id,
        account_sk,
        user_sk,
        created_date_sk,
        -- Degenerate dims needed for filtering without joining back
        division,
        region,
        is_won,
        is_open,
        fiscal_year,
        fiscal_quarter
    FROM {{ ref('fact_opportunities') }}
)

SELECT
    -- ── Surrogate key (own) ──────────────────────────────────────────────────
    {{ dbt_utils.generate_surrogate_key(['li.line_item_id']) }}     AS line_item_sk,

    -- ── Foreign keys ─────────────────────────────────────────────────────────
    o.opportunity_sk,
    o.account_sk,
    o.user_sk,
    o.created_date_sk                                               AS opportunity_date_sk,
    {{ dbt_utils.generate_surrogate_key(['li.product_id']) }}       AS product_sk,

    -- ── Natural keys ─────────────────────────────────────────────────────────
    li.line_item_id,
    li.opportunity_id,
    li.product_id,

    -- ── Degenerate dimensions (line-item level categoricals) ─────────────────
    li.line_item_name,
    li.line_item_type,
    li.unit_type,

    -- ── Measures ─────────────────────────────────────────────────────────────
    'USD'                                                           AS currency_code,
    li.unit_price,
    li.quantity,
    li.gross_amount,
    li.discount_applied_pct,
    li.net_amount,
    li.is_negotiated,
    li.created_date,

    -- ── Opportunity context (degenerate dims, avoids back-join in reports) ────
    o.division,
    o.region,
    o.is_won,
    o.is_open,
    o.fiscal_year,
    o.fiscal_quarter

FROM line_items li
LEFT JOIN opportunities o ON li.opportunity_id = o.opportunity_id
