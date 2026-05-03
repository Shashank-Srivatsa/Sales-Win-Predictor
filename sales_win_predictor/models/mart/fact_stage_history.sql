WITH stage_history AS (
    SELECT * FROM {{ ref('stg_crm_stage_history') }}
),

opportunities AS (
    SELECT
        opportunity_sk,
        opportunity_id,
        account_sk,
        user_sk,
        division,
        region,
        is_won,
        is_open,
        fiscal_year,
        fiscal_quarter
    FROM {{ ref('fact_opportunities') }}
)

SELECT
    -- Surrogate key (own)
    {{ dbt_utils.generate_surrogate_key(['sh.stage_history_id']) }} AS stage_history_sk,

    -- Foreign keys
    o.opportunity_sk,
    o.account_sk,
    o.user_sk,
    TO_NUMBER(TO_CHAR(sh.stage_entered_date, 'YYYYMMDD'))           AS stage_entered_date_sk,

    -- Natural key
    sh.stage_history_id,
    sh.opportunity_id,

    -- Stage transition details (degenerate dims)
    sh.from_stage,
    sh.to_stage,
    sh.stage_order,
    sh.stage_entered_date,
    sh.stage_exited_date,
    sh.changed_by_user_id,

    -- Measures
    sh.days_in_stage,
    sh.is_regression,

    -- Opportunity context (degenerate dims — avoids joining back to fact)
    o.division,
    o.region,
    o.is_won,
    o.is_open,
    o.fiscal_year,
    o.fiscal_quarter
FROM stage_history sh
LEFT JOIN opportunities o ON sh.opportunity_id = o.opportunity_id
