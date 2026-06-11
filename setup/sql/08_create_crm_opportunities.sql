-- =====================================================
-- Create: crm_opportunities Table
-- Source: crm_opportunities.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_opportunities (
    opportunity_id VARCHAR(50) NOT NULL,
    opportunity_name VARCHAR(255),
    account_id VARCHAR(50),
    primary_contact_id VARCHAR(50),
    owner_user_id VARCHAR(50),
    division VARCHAR(100),
    region VARCHAR(100),
    deal_type VARCHAR(100),
    lead_source VARCHAR(100),
    stage VARCHAR(100),
    amount DECIMAL(18, 2),
    discount_pct DECIMAL(5, 2),
    probability_manual DECIMAL(5, 2),
    created_date DATE,
    expected_close_date DATE,
    close_date_actual DATE,
    is_won INTEGER,
    lost_reason VARCHAR(255),
    is_renewal INTEGER,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    is_open INTEGER,
    PRIMARY KEY (opportunity_id),
    FOREIGN KEY (account_id) REFERENCES crm_accounts(account_id),
    FOREIGN KEY (primary_contact_id) REFERENCES crm_contacts(contact_id),
    FOREIGN KEY (owner_user_id) REFERENCES crm_users(user_id)
)
COMMENT = 'Sales opportunities (deals)';

-- Copy data from staged CSV
COPY INTO crm_opportunities
FROM @crm_stage/crm_opportunities.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_opportunities;
SELECT * FROM crm_opportunities LIMIT 5;
