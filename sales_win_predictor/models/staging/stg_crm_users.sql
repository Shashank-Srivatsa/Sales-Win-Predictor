WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_USERS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY USER_ID
            ORDER BY HIRE_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(USER_ID::VARCHAR))                               AS user_id,
        TRIM(FIRST_NAME::VARCHAR)                                   AS first_name,
        TRIM(LAST_NAME::VARCHAR)                                    AS last_name,
        TRIM(LOWER(EMAIL::VARCHAR))                                 AS email,
        TRIM(ROLE::VARCHAR)                                         AS role,
        TRIM(UPPER(DIVISION::VARCHAR))                              AS division,
        TRIM(UPPER(REGION::VARCHAR))                                AS region,
        COALESCE(SENIORITY_LEVEL::INT, {{ var('default_seniority_level') }})
                                                                    AS seniority_level,
        TRY_TO_DATE(HIRE_DATE::VARCHAR)                             AS hire_date,
        COALESCE(IS_ACTIVE::INT, {{ var('default_is_active_user') }})
                                                                    AS is_active,
        TRIM(UPPER(MANAGER_ID::VARCHAR))                            AS manager_id,
        COALESCE(TARGET_DEALS_PER_YEAR::INT, {{ var('default_target_deals') }})
                                                                    AS target_deals_per_year,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
