-- =====================================================
-- Create Stage for CSV File Upload
-- Execute this after database and schema setup
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

-- Create stage for storing CSV files
CREATE OR REPLACE STAGE crm_stage
  COMMENT = 'Stage for uploading CRM CSV files';

-- Create CSV file format
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  COMPRESSION = 'GZIP'
  FIELD_DELIMITER = ','
  RECORD_DELIMITER = '\n'
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('NULL', '')
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- Verify
SHOW STAGES;
SHOW FILE FORMATS;
