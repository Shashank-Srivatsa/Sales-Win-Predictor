WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_ACTIVITIES') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY ACTIVITY_ID
            ORDER BY ACTIVITY_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(ACTIVITY_ID::VARCHAR))                           AS activity_id,
        TRIM(UPPER(OPPORTUNITY_ID::VARCHAR))                        AS opportunity_id,
        TRIM(UPPER(USER_ID::VARCHAR))                               AS user_id,
        TRIM(ACTIVITY_TYPE::VARCHAR)                                AS activity_type,
        TRIM(SUBJECT::VARCHAR)                                      AS subject,
        TRY_TO_DATE(ACTIVITY_DATE::VARCHAR)                         AS activity_date,
        DURATION_MINUTES::INT                                       AS duration_minutes,
        TRIM(OUTCOME::VARCHAR)                                      AS outcome,
        COALESCE(IS_OUTBOUND::INT, 1)                               AS is_outbound,
        COALESCE(DAYS_SINCE_DEAL_CREATED::INT, 0)                   AS days_since_deal_created,

        CASE WHEN TRIM(UPPER(OUTCOME::VARCHAR)) ILIKE '%POSITIVE%' THEN 1 ELSE 0 END
                                                                    AS is_positive_outcome,
        CASE WHEN TRIM(UPPER(OUTCOME::VARCHAR)) ILIKE '%NEGATIVE%' THEN 1 ELSE 0 END
                                                                    AS is_negative_outcome,

        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
