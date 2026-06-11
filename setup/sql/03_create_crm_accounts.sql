-- =====================================================
-- Create: crm_accounts Table
-- Source: crm_accounts.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_accounts (
    account_id VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(100),
    annual_revenue_band VARCHAR(100),
    account_type VARCHAR(100),
    account_tier INTEGER,
    number_of_employees INTEGER,
    is_active INTEGER,
    created_date DATE,
    last_activity_date DATE,
    PRIMARY KEY (account_id)
)
COMMENT = 'Client company accounts';

-- Copy data from staged CSV
COPY INTO crm_accounts
FROM @crm_stage/crm_accounts.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_accounts;
SELECT * FROM crm_accounts LIMIT 5;
