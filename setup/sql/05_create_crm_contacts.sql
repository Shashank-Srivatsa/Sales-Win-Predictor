-- =====================================================
-- Create: crm_contacts Table
-- Source: crm_contacts.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_contacts (
    contact_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    job_title VARCHAR(100),
    department VARCHAR(100),
    is_primary_contact INTEGER,
    is_decision_maker INTEGER,
    created_date DATE,
    is_active INTEGER,
    PRIMARY KEY (contact_id),
    FOREIGN KEY (account_id) REFERENCES crm_accounts(account_id)
)
COMMENT = 'Contact people at client accounts';

-- Copy data from staged CSV
COPY INTO crm_contacts
FROM @crm_stage/crm_contacts.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_contacts;
SELECT * FROM crm_contacts LIMIT 5;
