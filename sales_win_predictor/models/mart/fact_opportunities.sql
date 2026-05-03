WITH opps AS (
    SELECT * FROM {{ ref('stg_crm_opportunities') }}
),

agent_perf AS (
    SELECT * FROM {{ ref('int_agent_performance') }}
),

users AS (
    SELECT user_id, division AS agent_division, seniority_level
    FROM {{ ref('stg_crm_users') }}
),

client_hist AS (
    SELECT * FROM {{ ref('int_client_deal_history') }}
),

activities AS (
    SELECT * FROM {{ ref('int_deal_activity_summary') }}
),

line_items AS (
    SELECT * FROM {{ ref('int_deal_line_item_summary') }}
),

stage_pivot AS (
    SELECT
        opportunity_id,
        SUM(CASE WHEN to_stage = 'Lead'          THEN days_in_stage ELSE 0 END) AS days_in_lead_stage,
        SUM(CASE WHEN to_stage = 'Qualified Lead' THEN days_in_stage ELSE 0 END) AS days_in_qualified_stage,
        SUM(CASE WHEN to_stage = 'Opportunity'   THEN days_in_stage ELSE 0 END) AS days_in_opportunity_stage,
        SUM(CASE WHEN to_stage = 'Negotiation'   THEN days_in_stage ELSE 0 END) AS days_in_negotiation_stage,
        SUM(is_regression)                                                       AS stage_regression_count
    FROM {{ ref('stg_crm_stage_history') }}
    GROUP BY opportunity_id
),

contracts AS (
    SELECT opportunity_id, number_of_revisions AS contract_revision_count
    FROM {{ ref('stg_crm_contracts') }}
)

SELECT
    -- ── Surrogate key (own) ──────────────────────────────────────────────────
    {{ dbt_utils.generate_surrogate_key(['o.opportunity_id']) }}    AS opportunity_sk,

    -- ── Foreign keys → dimension tables ─────────────────────────────────────
    {{ dbt_utils.generate_surrogate_key(['o.account_id']) }}        AS account_sk,
    {{ dbt_utils.generate_surrogate_key(['o.owner_user_id']) }}     AS user_sk,
    TO_NUMBER(TO_CHAR(o.created_date, 'YYYYMMDD'))                  AS created_date_sk,
    TO_NUMBER(TO_CHAR(o.expected_close_date, 'YYYYMMDD'))           AS expected_close_date_sk,
    CASE WHEN o.close_date_actual IS NOT NULL
         THEN TO_NUMBER(TO_CHAR(o.close_date_actual, 'YYYYMMDD'))
    END                                                             AS close_date_sk,

    -- ── Natural / business key (kept for traceability) ───────────────────────
    o.opportunity_id,

    -- ── Degenerate dimensions (deal-level categoricals, no own dim table) ────
    o.opportunity_name,
    o.division,
    o.region,
    o.deal_type,
    o.lead_source,
    o.stage,
    o.lost_reason,
    o.fiscal_year,
    o.fiscal_quarter,

    -- ── Core measures ────────────────────────────────────────────────────────
    o.amount,
    o.discount_pct,
    o.probability_manual,
    o.is_won,
    o.is_renewal,
    o.is_open,
    o.total_days_in_funnel,
    o.days_overdue,
    DATEDIFF('day', CURRENT_DATE, o.expected_close_date)            AS days_until_expected_close,
    CASE WHEN o.days_overdue > 0 AND o.is_open = 1 THEN 1 ELSE 0 END AS is_overdue,
    {{ fiscal_quarter_end('o.created_date') }}                      AS is_fiscal_quarter_end_period,

    -- ── Agent ML features (measures computed at deal snapshot time) ──────────
    COALESCE(ap.trailing_12m_win_rate, {{ var('default_win_rate') }})
                                                                    AS agent_trailing_12m_win_rate,
    COALESCE(u.seniority_level, {{ var('default_seniority_level') }})
                                                                    AS agent_seniority_level,
    COALESCE(ap.current_open_deals, {{ var('default_open_deals') }})
                                                                    AS agent_current_open_deals,
    CASE o.division
        WHEN 'TalentEdge'    THEN COALESCE(ap.win_rate_talentedge, {{ var('default_win_rate') }})
        WHEN 'CreativeMotion' THEN COALESCE(ap.win_rate_creativemotion, {{ var('default_win_rate') }})
        WHEN 'PulseMedia'    THEN COALESCE(ap.win_rate_pulsemedia, {{ var('default_win_rate') }})
        WHEN 'BrandVault'    THEN COALESCE(ap.win_rate_brandvault, {{ var('default_win_rate') }})
        ELSE {{ var('default_win_rate') }}
    END                                                             AS agent_win_rate_this_division,
    CASE WHEN u.agent_division = o.division THEN 1 ELSE 0 END       AS is_vertical_specialist,

    -- ── Client ML features ───────────────────────────────────────────────────
    COALESCE(ch.client_win_rate, {{ var('default_win_rate') }})     AS client_win_rate,
    COALESCE(ch.client_is_new, 1)                                   AS client_is_new,
    COALESCE(ch.total_lifetime_value, {{ var('default_open_deals') }})
                                                                    AS client_total_lifetime_value,
    ch.days_since_last_closed_deal                                  AS client_days_since_last_deal,

    -- ── Activity / engagement ML features ────────────────────────────────────
    COALESCE(a.total_activities, {{ var('default_total_activities') }})
                                                                    AS total_activities,
    a.days_since_last_activity,
    COALESCE(a.engagement_score, {{ var('default_win_rate') }})     AS engagement_score,
    COALESCE(a.positive_activity_ratio, {{ var('default_win_rate') }})
                                                                    AS positive_activity_ratio,

    -- ── Deal complexity ML features ───────────────────────────────────────────
    COALESCE(li.line_item_count, {{ var('default_total_activities') }})
                                                                    AS line_item_count,
    COALESCE(li.deal_complexity_score, {{ var('default_open_deals') }})
                                                                    AS deal_complexity_score,
    COALESCE(li.has_usage_rights, {{ var('default_open_deals') }})  AS has_usage_rights,
    COALESCE(li.has_minimum_guarantee, {{ var('default_open_deals') }})
                                                                    AS has_minimum_guarantee,

    -- ── Stage timing ML features ─────────────────────────────────────────────
    COALESCE(sp.days_in_lead_stage, {{ var('default_open_deals') }})
                                                                    AS days_in_lead_stage,
    COALESCE(sp.days_in_qualified_stage, {{ var('default_open_deals') }})
                                                                    AS days_in_qualified_stage,
    COALESCE(sp.days_in_opportunity_stage, {{ var('default_open_deals') }})
                                                                    AS days_in_opportunity_stage,
    COALESCE(sp.days_in_negotiation_stage, {{ var('default_open_deals') }})
                                                                    AS days_in_negotiation_stage,
    COALESCE(sp.stage_regression_count, {{ var('default_open_deals') }})
                                                                    AS stage_regression_count,

    -- ── Contract features ─────────────────────────────────────────────────────
    COALESCE(c.contract_revision_count, {{ var('default_contract_revisions') }})
                                                                    AS contract_revision_count

FROM opps o
LEFT JOIN agent_perf ap     ON o.owner_user_id = ap.agent_id
LEFT JOIN users u           ON o.owner_user_id = u.user_id
LEFT JOIN client_hist ch    ON o.account_id = ch.account_id
LEFT JOIN activities a      ON o.opportunity_id = a.opportunity_id
LEFT JOIN line_items li     ON o.opportunity_id = li.opportunity_id
LEFT JOIN stage_pivot sp    ON o.opportunity_id = sp.opportunity_id
LEFT JOIN contracts c       ON o.opportunity_id = c.opportunity_id
