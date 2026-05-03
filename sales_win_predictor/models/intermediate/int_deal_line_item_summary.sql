WITH line_items AS (
    SELECT
        opportunity_id,
        line_item_type,
        gross_amount,
        net_amount,
        discount_applied_pct,
        is_negotiated
    FROM {{ ref('stg_crm_line_items') }}
)

SELECT
    opportunity_id,
    COUNT(*)                                                        AS line_item_count,
    COUNT(DISTINCT line_item_type)                                  AS distinct_line_item_types,
    COUNT(*) * COUNT(DISTINCT line_item_type)                       AS deal_complexity_score,
    SUM(gross_amount)                                               AS total_gross_amount,
    SUM(net_amount)                                                 AS total_net_amount,
    MAX(discount_applied_pct)                                       AS max_line_item_discount,
    AVG(discount_applied_pct)                                       AS avg_line_item_discount,
    MAX(CASE WHEN line_item_type ILIKE '%Usage Rights%' THEN 1 ELSE 0 END)
                                                                    AS has_usage_rights,
    MAX(CASE WHEN line_item_type ILIKE '%Minimum Guarantee%'
              OR line_item_type ILIKE '%MG%' THEN 1 ELSE 0 END)    AS has_minimum_guarantee,
    COALESCE(SUM(is_negotiated), {{ var('default_negotiated_count') }})
                                                                    AS negotiated_item_count
FROM line_items
GROUP BY opportunity_id
