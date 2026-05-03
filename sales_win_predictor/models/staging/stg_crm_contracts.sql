WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_CONTRACTS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY CONTRACT_ID
            ORDER BY SIGNED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(CONTRACT_ID::VARCHAR))                           AS contract_id,
        TRIM(UPPER(OPPORTUNITY_ID::VARCHAR))                        AS opportunity_id,
        TRIM(UPPER(ACCOUNT_ID::VARCHAR))                            AS account_id,
        TRY_TO_DATE(CONTRACT_START_DATE::VARCHAR)                   AS contract_start_date,
        TRY_TO_DATE(CONTRACT_END_DATE::VARCHAR)                     AS contract_end_date,
        COALESCE(CONTRACT_DURATION_MONTHS::INT, {{ var('default_contract_duration_months') }})
                                                                    AS contract_duration_months,
        CONTRACT_VALUE::FLOAT                                       AS contract_value,
        TRIM(PAYMENT_TERMS::VARCHAR)                                AS payment_terms,
        TRY_TO_DATE(SIGNED_DATE::VARCHAR)                           AS signed_date,
        TRIM(UPPER(CONTRACT_STATUS::VARCHAR))                       AS contract_status,
        COALESCE(HAS_ROYALTY_CLAUSE::INT, {{ var('default_has_royalty') }})
                                                                    AS has_royalty_clause,
        ROYALTY_PCT::FLOAT                                          AS royalty_pct,
        ROYALTY_THRESHOLD_USD::FLOAT                                AS royalty_threshold_usd,
        COALESCE(NUMBER_OF_REVISIONS::INT, {{ var('default_contract_revisions') }})
                                                                    AS number_of_revisions,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
