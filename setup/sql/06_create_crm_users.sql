-- =====================================================
-- Create: crm_users Table
-- Source: crm_users.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_users (
    user_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    role VARCHAR(100),
    division VARCHAR(100),
    region VARCHAR(100),
    seniority_level VARCHAR(100),
    hire_date DATE,
    is_active INTEGER,
    manager_id VARCHAR(50),
    target_deals_per_year INTEGER,
    PRIMARY KEY (user_id)
)
COMMENT = 'Sales team members and users';

-- Copy data from staged CSV
COPY INTO crm_users
FROM @crm_stage/crm_users.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_users;
SELECT * FROM crm_users LIMIT 5;
