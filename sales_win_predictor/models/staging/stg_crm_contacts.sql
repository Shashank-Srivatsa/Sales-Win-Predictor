WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_CONTACTS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY CONTACT_ID
            ORDER BY CREATED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(CONTACT_ID::VARCHAR))                            AS contact_id,
        TRIM(UPPER(ACCOUNT_ID::VARCHAR))                            AS account_id,
        TRIM(FIRST_NAME::VARCHAR)                                   AS first_name,
        TRIM(LAST_NAME::VARCHAR)                                    AS last_name,
        TRIM(LOWER(EMAIL::VARCHAR))                                 AS email,
        TRIM(JOB_TITLE::VARCHAR)                                    AS job_title,
        TRIM(UPPER(DEPARTMENT::VARCHAR))                            AS department,
        COALESCE(IS_PRIMARY_CONTACT::INT, 0)                        AS is_primary_contact,
        COALESCE(IS_DECISION_MAKER::INT, 0)                         AS is_decision_maker,
        TRY_TO_DATE(CREATED_DATE::VARCHAR)                          AS created_date,
        COALESCE(IS_ACTIVE::INT, 1)                                 AS is_active,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
