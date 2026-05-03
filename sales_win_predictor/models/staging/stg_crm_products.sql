WITH source AS (
    SELECT * FROM {{ source('bronze', 'CRM_PRODUCTS') }}
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY PRODUCT_ID
            ORDER BY CREATED_DATE DESC
        ) AS _rn
    FROM source
),

cleaned AS (
    SELECT
        TRIM(UPPER(PRODUCT_ID::VARCHAR))                            AS product_id,
        TRIM(PRODUCT_NAME::VARCHAR)                                 AS product_name,
        TRIM(PRODUCT_CATEGORY::VARCHAR)                             AS product_category,
        CASE TRIM(UPPER(DIVISION::VARCHAR))
            WHEN 'TALENTEDGE'    THEN 'TalentEdge'
            WHEN 'CREATIVEMOTION' THEN 'CreativeMotion'
            WHEN 'PULSEMEDIA'    THEN 'PulseMedia'
            WHEN 'BRANDVAULT'    THEN 'BrandVault'
            ELSE TRIM(DIVISION::VARCHAR)
        END                                                         AS division,
        STANDARD_UNIT_PRICE::FLOAT                                  AS standard_unit_price,
        TRIM(LOWER(UNIT_TYPE::VARCHAR))                             AS unit_type,
        PRICE_RANGE_LOW::FLOAT                                      AS price_range_low,
        PRICE_RANGE_HIGH::FLOAT                                     AS price_range_high,
        COALESCE(IS_ACTIVE::INT, 1)                                 AS is_active,
        TRY_TO_DATE(CREATED_DATE::VARCHAR)                          AS catalogue_added_date,
        CURRENT_TIMESTAMP                                           AS _loaded_at
    FROM deduped
    WHERE _rn = 1
)

SELECT * FROM cleaned
