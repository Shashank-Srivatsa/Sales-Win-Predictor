-- =====================================================
-- Create: crm_opportunity_line_items Table
-- Source: crm_opportunity_line_items.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_opportunity_line_items (
    line_item_id VARCHAR(50) NOT NULL,
    opportunity_id VARCHAR(50),
    product_id VARCHAR(50),
    line_item_name VARCHAR(255),
    line_item_type VARCHAR(100),
    unit_type VARCHAR(50),
    unit_price DECIMAL(18, 2),
    quantity INTEGER,
    gross_amount DECIMAL(18, 2),
    discount_applied_pct DECIMAL(5, 2),
    net_amount DECIMAL(18, 2),
    is_negotiated INTEGER,
    created_date DATE,
    PRIMARY KEY (line_item_id),
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities(opportunity_id),
    FOREIGN KEY (product_id) REFERENCES crm_products(product_id)
)
COMMENT = 'Line items (products) in opportunities';

-- Copy data from staged CSV
COPY INTO crm_opportunity_line_items
FROM @crm_stage/crm_opportunity_line_items.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_opportunity_line_items;
SELECT * FROM crm_opportunity_line_items LIMIT 5;
