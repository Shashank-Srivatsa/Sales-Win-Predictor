-- =====================================================
-- Create: crm_opportunity_stage_history Table
-- Source: crm_opportunity_stage_history.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_opportunity_stage_history (
    stage_history_id VARCHAR(50) NOT NULL,
    opportunity_id VARCHAR(50),
    from_stage VARCHAR(100),
    to_stage VARCHAR(100),
    stage_entered_date DATE,
    stage_exited_date DATE,
    days_in_stage INTEGER,
    changed_by_user_id VARCHAR(50),
    is_regression INTEGER,
    PRIMARY KEY (stage_history_id),
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities(opportunity_id),
    FOREIGN KEY (changed_by_user_id) REFERENCES crm_users(user_id)
)
COMMENT = 'Deal stage progression history over time';

-- Copy data from staged CSV
COPY INTO crm_opportunity_stage_history
FROM @crm_stage/crm_opportunity_stage_history.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_opportunity_stage_history;
SELECT * FROM crm_opportunity_stage_history LIMIT 5;
