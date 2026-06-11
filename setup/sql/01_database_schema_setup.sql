-- =====================================================
-- Sales Win Predictor - Snowflake Setup
-- Database and Schema Creation
-- =====================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS sales_win_predictor
  COMMENT = 'Sales Win Predictor - CRM Data and Analytics';

-- Use the database
USE DATABASE sales_win_predictor;

-- Create Schemas
CREATE SCHEMA IF NOT EXISTS raw_crm_data
  COMMENT = 'Raw CRM data imported from CSV files';

CREATE SCHEMA IF NOT EXISTS processed_data
  COMMENT = 'Processed and transformed CRM data';

CREATE SCHEMA IF NOT EXISTS features
  COMMENT = 'Machine learning features and predictions';

-- Verify creation
SELECT CURRENT_DATABASE() AS database, CURRENT_SCHEMA() AS schema;

SHOW SCHEMAS IN DATABASE sales_win_predictor;
