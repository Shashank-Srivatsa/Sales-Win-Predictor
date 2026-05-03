WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_ACCOUNTS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY ACCOUNT_ID
            ORDER BY CREATED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(ACCOUNT_ID::VARCHAR))                            AS account_id,
        TRIM(ACCOUNT_NAME::VARCHAR)                                 AS account_name,
        TRIM(UPPER(INDUSTRY::VARCHAR))                              AS industry,
        TRIM(UPPER(COUNTRY::VARCHAR))                               AS country,
        TRIM(UPPER(REGION::VARCHAR))                                AS region,
        TRIM(UPPER(ANNUAL_REVENUE_BAND::VARCHAR))                   AS annual_revenue_band,
        TRIM(UPPER(ACCOUNT_TYPE::VARCHAR))                          AS account_type,
        COALESCE(ACCOUNT_TIER::INT, {{ var('default_account_tier') }})
                                                                    AS account_tier,
        COALESCE(NUMBER_OF_EMPLOYEES::INT, {{ var('default_number_of_employees') }})
                                                                    AS number_of_employees,
        COALESCE(IS_ACTIVE::INT, {{ var('default_is_active_account') }})
                                                                    AS is_active,
        TRY_TO_DATE(CREATED_DATE::VARCHAR)                          AS created_date,
        TRY_TO_DATE(LAST_ACTIVITY_DATE::VARCHAR)                    AS last_activity_date,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
