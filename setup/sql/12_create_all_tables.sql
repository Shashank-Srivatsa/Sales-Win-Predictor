-- =====================================================
-- ALL Tables Creation Script (Simplified)
-- Execute this single file to create all tables
-- No foreign key constraints to avoid dependency issues
-- =====================================================

USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

-- 1. CRM_ACCOUNTS
CREATE OR REPLACE TABLE crm_accounts (
    account_id VARCHAR(50) NOT NULL PRIMARY KEY,
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
    last_activity_date DATE
);

-- 2. CRM_USERS
CREATE OR REPLACE TABLE crm_users (
    user_id VARCHAR(50) NOT NULL PRIMARY KEY,
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
    target_deals_per_year INTEGER
);

-- 3. CRM_PRODUCTS
CREATE OR REPLACE TABLE crm_products (
    product_id VARCHAR(50) NOT NULL PRIMARY KEY,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    division VARCHAR(100),
    standard_unit_price DECIMAL(18, 2),
    unit_type VARCHAR(50),
    price_range_low DECIMAL(18, 2),
    price_range_high DECIMAL(18, 2),
    is_active INTEGER,
    created_date DATE
);

-- 4. CRM_CONTACTS
CREATE OR REPLACE TABLE crm_contacts (
    contact_id VARCHAR(50) NOT NULL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    job_title VARCHAR(100),
    department VARCHAR(100),
    is_primary_contact INTEGER,
    is_decision_maker INTEGER,
    created_date DATE,
    is_active INTEGER
);

-- 5. CRM_OPPORTUNITIES
CREATE OR REPLACE TABLE crm_opportunities (
    opportunity_id VARCHAR(50) NOT NULL PRIMARY KEY,
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
    is_open INTEGER
);

-- 6. CRM_ACTIVITIES
CREATE OR REPLACE TABLE crm_activities (
    activity_id VARCHAR(50) NOT NULL PRIMARY KEY,
    opportunity_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    activity_type VARCHAR(100),
    subject VARCHAR(500),
    activity_date DATE,
    duration_minutes INTEGER,
    outcome VARCHAR(100),
    is_outbound INTEGER,
    days_since_deal_created INTEGER
);

-- 7. CRM_CONTRACTS
CREATE OR REPLACE TABLE crm_contracts (
    contract_id VARCHAR(50) NOT NULL PRIMARY KEY,
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
    number_of_revisions INTEGER
);

-- 8. CRM_OPPORTUNITY_LINE_ITEMS
CREATE OR REPLACE TABLE crm_opportunity_line_items (
    line_item_id VARCHAR(50) NOT NULL PRIMARY KEY,
    opportunity_id VARCHAR(50),
    product_id VARCHAR(50),
    line_item_name VARCHAR(255),
    line_item_type VARCHAR(100),
    unit_type VARCHAR(50),
    unit_price DECIMAL(18, 2),
    quantity INTEGER,
    gross_amount DECIMAL(18, 2),
    discount_applied_pct DECIMAL(5, 2),
    net_amount DECIMAL(18, 2),
    is_negotiated INTEGER,
    created_date DATE
);

-- 9. CRM_OPPORTUNITY_STAGE_HISTORY
CREATE OR REPLACE TABLE crm_opportunity_stage_history (
    stage_history_id VARCHAR(50) NOT NULL PRIMARY KEY,
    opportunity_id VARCHAR(50),
    from_stage VARCHAR(100),
    to_stage VARCHAR(100),
    stage_entered_date DATE,
    stage_exited_date DATE,
    days_in_stage INTEGER,
    changed_by_user_id VARCHAR(50),
    is_regression INTEGER
);

SHOW TABLES;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'RAW_CRM_DATA'
ORDER BY TABLE_NAME;
