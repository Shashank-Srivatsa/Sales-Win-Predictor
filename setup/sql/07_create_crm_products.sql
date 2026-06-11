-- =====================================================
-- Create: crm_products Table
-- Source: crm_products.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_products (
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    division VARCHAR(100),
    standard_unit_price DECIMAL(18, 2),
    unit_type VARCHAR(50),
    price_range_low DECIMAL(18, 2),
    price_range_high DECIMAL(18, 2),
    is_active INTEGER,
    created_date DATE,
    PRIMARY KEY (product_id)
)
COMMENT = 'Product catalog';

-- Copy data from staged CSV
COPY INTO crm_products
FROM @crm_stage/crm_products.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_products;
SELECT * FROM crm_products LIMIT 5;
