WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_OPPORTUNITY_STAGE_HISTORY') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY STAGE_HISTORY_ID
            ORDER BY STAGE_ENTERED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(STAGE_HISTORY_ID::VARCHAR))                      AS stage_history_id,
        TRIM(UPPER(OPPORTUNITY_ID::VARCHAR))                        AS opportunity_id,
        TRIM(FROM_STAGE::VARCHAR)                                   AS from_stage,
        TRIM(TO_STAGE::VARCHAR)                                     AS to_stage,
        TRY_TO_DATE(STAGE_ENTERED_DATE::VARCHAR)                    AS stage_entered_date,
        TRY_TO_DATE(STAGE_EXITED_DATE::VARCHAR)                     AS stage_exited_date,

        COALESCE(
            DAYS_IN_STAGE::INT,
            DATEDIFF(
                'day',
                TRY_TO_DATE(STAGE_ENTERED_DATE::VARCHAR),
                COALESCE(TRY_TO_DATE(STAGE_EXITED_DATE::VARCHAR), CURRENT_DATE)
            )
        )                                                           AS days_in_stage,

        TRIM(UPPER(CHANGED_BY_USER_ID::VARCHAR))                    AS changed_by_user_id,
        COALESCE(IS_REGRESSION::INT, 0)                             AS is_regression,

        CASE TRIM(TO_STAGE::VARCHAR)
            WHEN 'Lead'          THEN 1
            WHEN 'Qualified Lead' THEN 2
            WHEN 'Opportunity'   THEN 3
            WHEN 'Negotiation'   THEN 4
            WHEN 'Closed Won'    THEN 5
            WHEN 'Closed Lost'   THEN 5
            ELSE 0
        END                                                         AS stage_order,

        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
