-- =====================================================
-- Create: crm_activities Table
-- Source: crm_activities.csv
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

CREATE OR REPLACE TABLE crm_activities (
    activity_id VARCHAR(50) NOT NULL,
    opportunity_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    activity_type VARCHAR(100),
    subject VARCHAR(500),
    activity_date DATE,
    duration_minutes INTEGER,
    outcome VARCHAR(100),
    is_outbound INTEGER,
    days_since_deal_created INTEGER,
    PRIMARY KEY (activity_id),
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities(opportunity_id),
    FOREIGN KEY (user_id) REFERENCES crm_users(user_id)
)
COMMENT = 'Sales activities: calls, emails, meetings associated with opportunities';

-- Copy data from staged CSV
COPY INTO crm_activities
FROM @crm_stage/crm_activities.csv.gz
FILE_FORMAT = (
    FORMAT_NAME = 'csv_format'
    PARSE_HEADER = TRUE
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Verify
SELECT COUNT(*) as row_count FROM crm_activities;
SELECT * FROM crm_activities LIMIT 5;
