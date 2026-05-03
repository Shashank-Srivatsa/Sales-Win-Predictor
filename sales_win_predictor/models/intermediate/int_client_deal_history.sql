WITH deals AS (
    SELECT
        account_id,
        opportunity_id,
        amount,
        is_won,
        is_open,
        division,
        region,
        close_date_actual,
        total_days_in_funnel
    FROM {{ ref('stg_crm_opportunities') }}
),

closed AS (
    SELECT * FROM deals WHERE is_won IS NOT NULL
),

won AS (
    SELECT * FROM deals WHERE is_won = 1
),

open_deals AS (
    SELECT
        account_id,
        COUNT(*) AS total_active_deals
    FROM deals
    WHERE is_open = 1
    GROUP BY account_id
),

last_close AS (
    SELECT
        account_id,
        MAX(close_date_actual) AS last_closed_date
    FROM closed
    GROUP BY account_id
),

division_mode AS (
    SELECT
        account_id,
        division,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM deals
    GROUP BY account_id, division
),

region_mode AS (
    SELECT
        account_id,
        region,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM deals
    GROUP BY account_id, region
)

SELECT
    c.account_id,
    COUNT(c.opportunity_id)                                         AS total_deals_ever,
    SUM(c.is_won)                                                   AS total_won_deals,
    {{ safe_divide('SUM(c.is_won)', 'COUNT(c.opportunity_id)') }}   AS client_win_rate,
    CASE WHEN SUM(c.is_won) = 0 THEN 1 ELSE 0 END                  AS client_is_new,
    SUM(CASE WHEN c.is_won = 1 THEN c.amount ELSE 0 END)           AS total_lifetime_value,
    AVG(c.amount)                                                   AS avg_deal_value,
    DATEDIFF('day', lc.last_closed_date, CURRENT_DATE)              AS days_since_last_closed_deal,
    COALESCE(od.total_active_deals, {{ var('default_open_deals') }})
                                                                    AS total_active_deals,
    dm.division                                                     AS most_common_division,
    rm.region                                                       AS client_preferred_region
FROM closed c
LEFT JOIN last_close lc   ON c.account_id = lc.account_id
LEFT JOIN open_deals od   ON c.account_id = od.account_id
LEFT JOIN division_mode dm ON c.account_id = dm.account_id AND dm.rn = 1
LEFT JOIN region_mode rm  ON c.account_id = rm.account_id AND rm.rn = 1
GROUP BY
    c.account_id,
    lc.last_closed_date,
    od.total_active_deals,
    dm.division,
    rm.region
