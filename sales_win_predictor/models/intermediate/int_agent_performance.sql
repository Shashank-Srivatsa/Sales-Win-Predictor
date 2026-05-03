WITH closed_deals AS (
    SELECT
        owner_user_id,
        division,
        amount,
        is_won,
        total_days_in_funnel,
        close_date_actual,
        is_open
    FROM {{ ref('stg_crm_opportunities') }}
    WHERE is_won IS NOT NULL
),

open_deals AS (
    SELECT
        owner_user_id,
        COUNT(*) AS current_open_deals
    FROM {{ ref('stg_crm_opportunities') }}
    WHERE is_open = 1
    GROUP BY owner_user_id
),

trailing_12m AS (
    SELECT
        owner_user_id,
        COUNT(*)                                        AS trailing_12m_closed_deals,
        SUM(is_won)                                     AS trailing_12m_won_deals
    FROM closed_deals
    WHERE close_date_actual >= DATEADD('month', -12, CURRENT_DATE)
    GROUP BY owner_user_id
),

division_win_rates AS (
    SELECT
        owner_user_id,
        SUM(CASE WHEN division = 'TalentEdge'    AND is_won = 1 THEN 1 ELSE 0 END) AS won_talentedge,
        SUM(CASE WHEN division = 'TalentEdge'    AND is_won IS NOT NULL THEN 1 ELSE 0 END) AS closed_talentedge,
        SUM(CASE WHEN division = 'CreativeMotion' AND is_won = 1 THEN 1 ELSE 0 END) AS won_creativemotion,
        SUM(CASE WHEN division = 'CreativeMotion' AND is_won IS NOT NULL THEN 1 ELSE 0 END) AS closed_creativemotion,
        SUM(CASE WHEN division = 'PulseMedia'    AND is_won = 1 THEN 1 ELSE 0 END) AS won_pulsemedia,
        SUM(CASE WHEN division = 'PulseMedia'    AND is_won IS NOT NULL THEN 1 ELSE 0 END) AS closed_pulsemedia,
        SUM(CASE WHEN division = 'BrandVault'    AND is_won = 1 THEN 1 ELSE 0 END) AS won_brandvault,
        SUM(CASE WHEN division = 'BrandVault'    AND is_won IS NOT NULL THEN 1 ELSE 0 END) AS closed_brandvault
    FROM closed_deals
    GROUP BY owner_user_id
),

overall AS (
    SELECT
        owner_user_id,
        COUNT(*)                                        AS total_closed_deals,
        SUM(is_won)                                     AS total_won_deals,
        {{ safe_divide('SUM(is_won)', 'COUNT(*)') }}    AS overall_win_rate,
        AVG(CASE WHEN is_won = 1 THEN amount END)       AS avg_deal_value_won,
        AVG(CASE WHEN is_won = 1 THEN total_days_in_funnel END) AS avg_days_to_close_won
    FROM closed_deals
    GROUP BY owner_user_id
)

SELECT
    o.owner_user_id                                                 AS agent_id,
    o.total_closed_deals,
    o.total_won_deals,
    o.overall_win_rate,
    COALESCE(t.trailing_12m_closed_deals, {{ var('default_total_deals') }})
                                                                    AS trailing_12m_closed_deals,
    COALESCE(t.trailing_12m_won_deals, {{ var('default_total_deals') }})
                                                                    AS trailing_12m_won_deals,
    {{ safe_divide('COALESCE(t.trailing_12m_won_deals, 0)', 'COALESCE(t.trailing_12m_closed_deals, 0)') }}
                                                                    AS trailing_12m_win_rate,
    o.avg_deal_value_won,
    o.avg_days_to_close_won,
    COALESCE(od.current_open_deals, {{ var('default_open_deals') }})
                                                                    AS current_open_deals,
    {{ safe_divide('d.won_talentedge', 'd.closed_talentedge') }}    AS win_rate_talentedge,
    {{ safe_divide('d.won_creativemotion', 'd.closed_creativemotion') }} AS win_rate_creativemotion,
    {{ safe_divide('d.won_pulsemedia', 'd.closed_pulsemedia') }}    AS win_rate_pulsemedia,
    {{ safe_divide('d.won_brandvault', 'd.closed_brandvault') }}    AS win_rate_brandvault
FROM overall o
LEFT JOIN trailing_12m t      ON o.owner_user_id = t.owner_user_id
LEFT JOIN open_deals od        ON o.owner_user_id = od.owner_user_id
LEFT JOIN division_win_rates d ON o.owner_user_id = d.owner_user_id
