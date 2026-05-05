WITH products AS (
    SELECT * FROM {{ ref('stg_crm_products') }}
)

SELECT
    -- ── Surrogate key ────────────────────────────────────────────────────────
    {{ dbt_utils.generate_surrogate_key(['product_id']) }}  AS product_sk,

    -- ── Natural key ──────────────────────────────────────────────────────────
    product_id,

    -- ── Descriptive attributes ───────────────────────────────────────────────
    product_name,
    product_category,
    division,
    unit_type,

    -- ── Pricing ──────────────────────────────────────────────────────────────
    standard_unit_price,
    price_range_low,
    price_range_high,

    -- ── Status ───────────────────────────────────────────────────────────────
    is_active,
    catalogue_added_date

FROM products
