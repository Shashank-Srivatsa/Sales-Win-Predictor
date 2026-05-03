WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_OPPURTUNITY_LINE_ITEMS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY LINE_ITEM_ID
            ORDER BY CREATED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(LINE_ITEM_ID::VARCHAR))                          AS line_item_id,
        TRIM(UPPER(OPPORTUNITY_ID::VARCHAR))                        AS opportunity_id,
        TRIM(UPPER(PRODUCT_ID::VARCHAR))                            AS product_id,
        TRIM(LINE_ITEM_NAME::VARCHAR)                               AS line_item_name,
        TRIM(LINE_ITEM_TYPE::VARCHAR)                               AS line_item_type,
        TRIM(LOWER(UNIT_TYPE::VARCHAR))                             AS unit_type,
        UNIT_PRICE::FLOAT                                           AS unit_price,
        QUANTITY::INT                                               AS quantity,
        GROSS_AMOUNT::FLOAT                                         AS gross_amount,
        DISCOUNT_APPLIED_PCT::FLOAT                                 AS discount_applied_pct,
        NET_AMOUNT::FLOAT                                           AS net_amount,
        COALESCE(IS_NEGOTIATED::INT, {{ var('default_is_negotiated_item') }})
                                                                    AS is_negotiated,
        TRY_TO_DATE(CREATED_DATE::VARCHAR)                          AS created_date,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
