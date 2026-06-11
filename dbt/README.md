# 🔄 dbt: Data Transformation Layer

Transform raw CRM data into refined analytical tables using dbt (data build tool).

---

## 📋 Overview

dbt handles:
- Cleaning raw data
- Creating dimensional tables
- Building aggregations
- Running tests and validations
- Maintaining data lineage

**Output**: Clean, tested data ready for ML modeling and reporting

---

## ✅ Prerequisites

Before starting, ensure you have:
- ✅ Snowflake database with raw CRM data loaded (see [setup/](../setup/))
- ✅ Python virtual environment activated
- ✅ dbt installed: `pip install dbt-snowflake`

---

## 🛠️ Step 1: Configure dbt

### 1.1 Create dbt Project Structure

If not already created, initialize a dbt project:

```bash
cd Sales-Win-Predictor
dbt init sales_win_predictor  # Creates dbt project folder
```

### 1.2 Configure Snowflake Connection

Edit `~/.dbt/profiles.yml` (or `dbt_profiles.yml` in project):

```yaml
sales_win_predictor:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: xy12345-ab67890          # Your account identifier
      user: your_username
      password: your_password
      role: TRANSFORMER                 # Create this role in Snowflake
      database: sales_win_predictor
      schema: dbt_dev                   # dbt creates this
      warehouse: COMPUTE_WH
      threads: 4
      client_session_keep_alive: False

    prod:
      type: snowflake
      account: xy12345-ab67890
      user: your_username
      password: your_password
      role: TRANSFORMER
      database: sales_win_predictor
      schema: dbt_prod
      warehouse: COMPUTE_WH
      threads: 4
      client_session_keep_alive: False
```

**Note**: Replace with your Snowflake credentials

### 1.3 Create dbt Role in Snowflake

Run in Snowflake:

```sql
-- Create TRANSFORMER role
CREATE ROLE IF NOT EXISTS TRANSFORMER;

-- Grant permissions to role
GRANT USAGE ON DATABASE sales_win_predictor TO ROLE TRANSFORMER;
GRANT USAGE ON SCHEMA sales_win_predictor.raw_crm_data TO ROLE TRANSFORMER;
GRANT USAGE ON SCHEMA sales_win_predictor.dbt_dev TO ROLE TRANSFORMER;
GRANT USAGE ON SCHEMA sales_win_predictor.dbt_prod TO ROLE TRANSFORMER;

GRANT CREATE SCHEMA ON DATABASE sales_win_predictor TO ROLE TRANSFORMER;
GRANT CREATE TABLE ON SCHEMA sales_win_predictor.dbt_dev TO ROLE TRANSFORMER;
GRANT CREATE TABLE ON SCHEMA sales_win_predictor.dbt_prod TO ROLE TRANSFORMER;

-- Assign role to dbt user
GRANT ROLE TRANSFORMER TO USER your_username;
```

### 1.4 Test Connection

```bash
dbt debug
```

Expected output:
```
Connection test: [OK successfully authenticated]
```

---

## 📊 Step 2: Set Up dbt Models

### 2.1 Directory Structure

```
dbt/
├── models/
│   ├── staging/
│   │   ├── stg_crm_accounts.sql
│   │   ├── stg_crm_opportunities.sql
│   │   ├── stg_crm_activities.sql
│   │   └── ...
│   ├── marts/
│   │   ├── fct_opportunities.sql
│   │   ├── dim_accounts.sql
│   │   ├── dim_users.sql
│   │   └── fct_activities_summary.sql
│   └── intermediate/
│       └── int_opportunity_features.sql
├── tests/
│   ├── not_null_tests.sql
│   └── relationship_tests.sql
├── macros/
├── dbt_project.yml
└── profiles.yml
```

### 2.2 Create Staging Models

**dbt/models/staging/stg_crm_accounts.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['staging', 'crm']
) }}

SELECT
    account_id,
    account_name,
    industry,
    country,
    region,
    annual_revenue_band,
    account_type,
    account_tier,
    number_of_employees,
    is_active,
    created_date,
    last_activity_date,
    CURRENT_TIMESTAMP() as dbt_loaded_at
FROM {{ source('raw_crm', 'crm_accounts') }}
WHERE is_active = 1
```

**dbt/models/staging/stg_crm_opportunities.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['staging', 'crm']
) }}

SELECT
    opportunity_id,
    opportunity_name,
    account_id,
    primary_contact_id,
    owner_user_id,
    stage,
    amount,
    discount_pct,
    is_won,
    created_date,
    close_date_actual,
    is_open,
    DATEDIFF(day, created_date, CURRENT_DATE()) as days_open,
    CURRENT_TIMESTAMP() as dbt_loaded_at
FROM {{ source('raw_crm', 'crm_opportunities') }}
```

**dbt/models/staging/stg_crm_activities.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['staging', 'crm']
) }}

SELECT
    activity_id,
    opportunity_id,
    user_id,
    activity_type,
    activity_date,
    duration_minutes,
    outcome,
    is_outbound,
    CURRENT_TIMESTAMP() as dbt_loaded_at
FROM {{ source('raw_crm', 'crm_activities') }}
WHERE activity_date IS NOT NULL
```

### 2.3 Create Mart Models

**dbt/models/marts/fct_opportunities.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['mart', 'fact']
) }}

SELECT
    opp.opportunity_id,
    opp.opportunity_name,
    opp.account_id,
    opp.owner_user_id,
    opp.stage,
    opp.amount,
    opp.discount_pct,
    opp.is_won,
    opp.is_open,
    opp.created_date,
    opp.close_date_actual,
    opp.days_open,
    acc.industry,
    acc.region,
    COALESCE(act_summary.total_activities, 0) as total_activities,
    COALESCE(act_summary.total_meeting_minutes, 0) as total_meeting_minutes
FROM {{ ref('stg_crm_opportunities') }} opp
LEFT JOIN {{ ref('stg_crm_accounts') }} acc
    ON opp.account_id = acc.account_id
LEFT JOIN {{ ref('int_activity_summary') }} act_summary
    ON opp.opportunity_id = act_summary.opportunity_id
```

**dbt/models/marts/dim_accounts.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['mart', 'dimension']
) }}

SELECT
    account_id,
    account_name,
    industry,
    country,
    region,
    annual_revenue_band,
    account_tier,
    number_of_employees,
    is_active
FROM {{ ref('stg_crm_accounts') }}
```

### 2.4 Create Intermediate Models

**dbt/models/intermediate/int_activity_summary.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_dev',
    tags=['intermediate']
) }}

SELECT
    opportunity_id,
    COUNT(*) as total_activities,
    SUM(duration_minutes) as total_meeting_minutes,
    MAX(activity_date) as last_activity_date
FROM {{ ref('stg_crm_activities') }}
GROUP BY opportunity_id
```

### 2.5 Configure Sources

**dbt/models/sources.yml**:

```yaml
version: 2

sources:
  - name: raw_crm
    description: Raw CRM data from Salesforce export
    database: sales_win_predictor
    schema: raw_crm_data
    tables:
      - name: crm_accounts
        description: Client accounts
        columns:
          - name: account_id
            description: Unique account identifier
            tests:
              - unique
              - not_null

      - name: crm_opportunities
        description: Sales opportunities (deals)
        columns:
          - name: opportunity_id
            description: Unique opportunity identifier
            tests:
              - unique
              - not_null
          - name: account_id
            description: Reference to account
            tests:
              - relationships:
                  to: source('raw_crm', 'crm_accounts')
                  field: account_id

      - name: crm_activities
        description: Sales activities
        columns:
          - name: activity_id
            tests:
              - unique
              - not_null
```

---

## 🏃 Step 3: Run dbt Models

### 3.1 Development Workflow

```bash
# Parse all models (verify syntax)
dbt parse

# Run models in development schema
dbt run --target dev

# Expected output:
# Running with dbt X.X.X
# Found 15 models...
# Building model stg_crm_accounts...
# Building model fct_opportunities...
# ✓ 15 of 15 OK created table
```

### 3.2 Run Specific Models

```bash
# Run only staging models
dbt run --select tag:staging

# Run only a specific model
dbt run --select stg_crm_accounts

# Run a model and its children
dbt run --select fct_opportunities+
```

---

## ✅ Step 4: Test Models

### 4.1 Run Tests

```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test --select stg_crm_accounts

# Expected output:
# Testing not_null_account_id... PASS
# Testing unique_account_id... PASS
# ✓ All tests passed
```

### 4.2 Add Custom Tests

**dbt/tests/check_opportunity_amounts.sql**:

```sql
-- Opportunities should have positive amounts
SELECT opportunity_id, amount
FROM {{ ref('fct_opportunities') }}
WHERE amount <= 0
  AND is_won = 1
```

Run test:
```bash
dbt test --select check_opportunity_amounts
```

---

## 📈 Step 5: Generate Documentation

```bash
# Generate dbt docs
dbt docs generate

# Serve documentation (opens in browser)
dbt docs serve
```

Docs show:
- Model lineage
- Column descriptions
- Test results
- Data freshness

---

## 🚀 Step 6: Deploy to Production

### 6.1 Create Prod Schema in Snowflake

```sql
CREATE SCHEMA IF NOT EXISTS sales_win_predictor.dbt_prod;
```

### 6.2 Deploy Models

```bash
# Run dbt with production target
dbt run --target prod

# Create snapshots for historical tracking
dbt snapshot --target prod
```

### 6.3 Schedule dbt Runs (Optional)

Using external scheduler (cron, Airflow, dbt Cloud):

```bash
# Run daily at 2 AM
dbt run --target prod && dbt test --target prod
```

---

## 📊 Verify Results in Snowflake

```sql
USE DATABASE sales_win_predictor;

-- Check dbt-created tables
SHOW TABLES IN SCHEMA dbt_dev;

-- Check row counts
SELECT 'stg_crm_accounts' as table_name, COUNT(*) as row_count 
FROM dbt_dev.stg_crm_accounts
UNION ALL
SELECT 'fct_opportunities', COUNT(*) FROM dbt_dev.fct_opportunities;

-- Check data quality
SELECT stage, is_won, COUNT(*) as cnt, AVG(amount) as avg_amount
FROM dbt_dev.fct_opportunities
GROUP BY stage, is_won;
```

---

## 🐛 Troubleshooting

### Error: "Connection test: [ERROR]"
```bash
# Check profiles.yml location
dbt debug --profiles-dir ~/.dbt

# Verify Snowflake credentials
```

### Error: "Schema does not exist"
```sql
-- In Snowflake, create schema manually
CREATE SCHEMA sales_win_predictor.dbt_dev;
GRANT USAGE ON SCHEMA dbt_dev TO ROLE TRANSFORMER;
```

### Models not appearing after `dbt run`
```bash
# Check for SQL syntax errors
dbt parse

# Run with verbose logging
dbt run --debug
```

---

## 📝 Next Steps

After dbt models are complete:

1. ✅ Proceed to [features/](../features/) to create ML feature tables
2. Verify dbt models in Snowflake
3. Generate documentation with `dbt docs generate`

---

## 📚 Additional Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Snowflake dbt Adapter](https://docs.getdbt.com/reference/warehouse-setups/snowflake-setup)

---

## ✨ Key dbt Commands Reference

```bash
dbt init project_name        # Create new project
dbt debug                    # Test connection
dbt parse                    # Validate syntax
dbt run                      # Execute models
dbt test                     # Run tests
dbt docs generate            # Create docs
dbt docs serve               # View docs locally
dbt freshness                # Check data freshness
dbt source freshness         # Check source freshness
dbt snapshot                 # Create historical snapshots
dbt seed                     # Load seed data
```

