WITH users AS (
    SELECT * FROM {{ ref('stg_crm_users') }}
),

agent_perf AS (
    SELECT * FROM {{ ref('int_agent_performance') }}
)

SELECT
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['u.user_id']) }}           AS user_sk,

    -- Natural / business key
    u.user_id,

    -- Descriptive attributes
    u.first_name || ' ' || u.last_name                             AS full_name,
    u.first_name,
    u.last_name,
    u.email,
    u.role,
    u.division,
    u.region,
    u.seniority_level,
    u.hire_date,
    u.is_active,
    u.manager_id,
    u.target_deals_per_year,

    -- Enriched performance metrics
    COALESCE(p.total_closed_deals, 0)                               AS total_closed_deals,
    COALESCE(p.total_won_deals, 0)                                  AS total_won_deals,
    COALESCE(p.overall_win_rate, 0)                                 AS overall_win_rate,
    COALESCE(p.trailing_12m_win_rate, 0)                            AS trailing_12m_win_rate,
    COALESCE(p.trailing_12m_closed_deals, 0)                        AS trailing_12m_closed_deals,
    COALESCE(p.current_open_deals, 0)                               AS current_open_deals,
    p.avg_deal_value_won,
    p.avg_days_to_close_won,
    COALESCE(p.win_rate_talentedge, 0)                              AS win_rate_talentedge,
    COALESCE(p.win_rate_creativemotion, 0)                          AS win_rate_creativemotion,
    COALESCE(p.win_rate_pulsemedia, 0)                              AS win_rate_pulsemedia,
    COALESCE(p.win_rate_brandvault, 0)                              AS win_rate_brandvault
FROM users u
LEFT JOIN agent_perf p ON u.user_id = p.agent_id
