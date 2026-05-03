WITH accounts AS (
    SELECT * FROM {{ ref('stg_crm_accounts') }}
),

client_history AS (
    SELECT * FROM {{ ref('int_client_deal_history') }}
)

SELECT
    -- Surrogate key (stable hash of the natural key)
    {{ dbt_utils.generate_surrogate_key(['a.account_id']) }}        AS account_sk,

    -- Natural / business key (kept for traceability and joining to Bronze)
    a.account_id,

    -- Descriptive attributes
    a.account_name,
    a.industry,
    a.country,
    a.region,
    a.annual_revenue_band,
    a.account_type,
    a.account_tier,
    a.number_of_employees,
    a.is_active,
    a.created_date,
    a.last_activity_date,

    -- Enriched client history metrics
    COALESCE(h.total_deals_ever, 0)                                 AS total_deals_ever,
    COALESCE(h.total_won_deals, 0)                                  AS total_won_deals,
    COALESCE(h.client_win_rate, 0)                                  AS client_win_rate,
    COALESCE(h.client_is_new, 1)                                    AS client_is_new,
    COALESCE(h.total_lifetime_value, 0)                             AS total_lifetime_value,
    h.avg_deal_value,
    h.days_since_last_closed_deal,
    COALESCE(h.total_active_deals, 0)                               AS total_active_deals,
    h.most_common_division,
    h.client_preferred_region
FROM accounts a
LEFT JOIN client_history h ON a.account_id = h.account_id
