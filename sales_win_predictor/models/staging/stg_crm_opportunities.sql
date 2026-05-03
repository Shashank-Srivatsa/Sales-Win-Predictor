WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_OPPORTUNITIES') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY OPPORTUNITY_ID
            ORDER BY CREATED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(OPPORTUNITY_ID::VARCHAR))                        AS opportunity_id,
        TRIM(OPPORTUNITY_NAME::VARCHAR)                             AS opportunity_name,
        TRIM(UPPER(ACCOUNT_ID::VARCHAR))                            AS account_id,
        TRIM(UPPER(PRIMARY_CONTACT_ID::VARCHAR))                    AS primary_contact_id,
        TRIM(UPPER(OWNER_USER_ID::VARCHAR))                         AS owner_user_id,

        CASE TRIM(UPPER(DIVISION::VARCHAR))
            WHEN 'TALENTEDGE'    THEN 'TalentEdge'
            WHEN 'CREATIVEMOTION' THEN 'CreativeMotion'
            WHEN 'PULSEMEDIA'    THEN 'PulseMedia'
            WHEN 'BRANDVAULT'    THEN 'BrandVault'
            ELSE TRIM(DIVISION::VARCHAR)
        END                                                         AS division,

        TRIM(UPPER(REGION::VARCHAR))                                AS region,
        TRIM(DEAL_TYPE::VARCHAR)                                    AS deal_type,
        TRIM(LEAD_SOURCE::VARCHAR)                                  AS lead_source,
        TRIM(STAGE::VARCHAR)                                        AS stage,
        AMOUNT::FLOAT                                               AS amount,
        COALESCE(DISCOUNT_PCT::FLOAT, {{ var('default_discount_pct') }})
                                                                    AS discount_pct,
        PROBABILITY_MANUAL::INT                                     AS probability_manual,
        TRY_TO_DATE(CREATED_DATE::VARCHAR)                          AS created_date,
        TRY_TO_DATE(EXPECTED_CLOSE_DATE::VARCHAR)                   AS expected_close_date,
        TRY_TO_DATE(CLOSE_DATE_ACTUAL::VARCHAR)                     AS close_date_actual,
        IS_WON::INT                                                 AS is_won,    -- NULL for open deals — do NOT coalesce
        TRIM(LOST_REASON::VARCHAR)                                  AS lost_reason,
        COALESCE(IS_RENEWAL::INT, {{ var('default_is_renewal') }})  AS is_renewal,
        FISCAL_YEAR::INT                                            AS fiscal_year,
        TRIM(FISCAL_QUARTER::VARCHAR)                               AS fiscal_quarter,
        COALESCE(IS_OPEN::INT, {{ var('default_is_open') }})        AS is_open,

        DATEDIFF(
            'day',
            TRY_TO_DATE(CREATED_DATE::VARCHAR),
            COALESCE(TRY_TO_DATE(CLOSE_DATE_ACTUAL::VARCHAR), CURRENT_DATE)
        )                                                           AS total_days_in_funnel,

        DATEDIFF(
            'day',
            TRY_TO_DATE(EXPECTED_CLOSE_DATE::VARCHAR),
            CURRENT_DATE
        )                                                           AS days_overdue,

        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
