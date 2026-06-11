-- =====================================================
-- Create: crm_contracts Table
-- Source: crm_contracts.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_contracts (
    contract_id VARCHAR(50) NOT NULL,
    opportunity_id VARCHAR(50),
    account_id VARCHAR(50),
    contract_start_date DATE,
    contract_end_date DATE,
    contract_duration_months INTEGER,
    contract_value DECIMAL(18, 2),
    payment_terms VARCHAR(100),
    signed_date DATE,
    contract_status VARCHAR(100),
    has_royalty_clause INTEGER,
    royalty_pct DECIMAL(5, 2),
    royalty_threshold_usd DECIMAL(18, 2),
    number_of_revisions INTEGER,
    PRIMARY KEY (contract_id),
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities(opportunity_id),
    FOREIGN KEY (account_id) REFERENCES crm_accounts(account_id)
)
COMMENT = 'Executed contracts linked to won deals';

-- Copy data from staged CSV
COPY INTO crm_contracts
FROM @crm_stage/crm_contracts.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_contracts;
SELECT * FROM crm_contracts LIMIT 5;
