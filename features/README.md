# 🎯 Feature Engineering: ML-Ready Data Layer

Create features for machine learning models that predict deal outcomes.

---

## 📋 Overview

This layer:
- Aggregates deal-level metrics
- Engineers features from raw data
- Creates time-series features
- Handles missing values
- Produces feature tables for ML

**Output**: Feature tables in `features` schema ready for ML training

---

## ✅ Prerequisites

- ✅ dbt models complete (see [dbt/](../dbt/))
- ✅ Snowflake database with cleaned data
- ✅ Python + pandas, numpy installed

---

## 📊 Feature Engineering Architecture

### Feature Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| **Deal Features** | amount, discount, days_open | Deal characteristics |
| **Account Features** | revenue_band, industry, region | Customer profile |
| **Activity Features** | total_calls, last_activity_days | Engagement level |
| **Stage Features** | days_in_stage, stage_changes | Deal progression |
| **User Features** | rep_experience, targets_met | Sales rep metrics |

---

## 🛠️ Step 1: Set Up Feature Engineering Environment

### 1.1 Python Script for Feature Creation

**features/create_features.py**:

```python
import snowflake.connector
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def get_snowflake_connection():
    """Create Snowflake connection."""
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='features'
    )

def create_feature_schema(conn):
    """Create features schema if not exists."""
    cursor = conn.cursor()
    cursor.execute("CREATE SCHEMA IF NOT EXISTS sales_win_predictor.features")
    cursor.close()

def create_deal_features(conn):
    """Create deal-level feature table."""
    query = """
    CREATE OR REPLACE TABLE fea_opportunities AS
    SELECT
        -- Primary key
        opp.opportunity_id,
        opp.account_id,
        opp.owner_user_id,
        
        -- Target variable
        opp.is_won as target,
        
        -- Deal Amount Features
        opp.amount,
        opp.discount_pct,
        CASE 
            WHEN opp.amount < 10000 THEN 'Small'
            WHEN opp.amount < 50000 THEN 'Medium'
            WHEN opp.amount < 100000 THEN 'Large'
            ELSE 'Enterprise'
        END as deal_size_category,
        
        -- Deal Timing Features
        DATEDIFF(day, opp.created_date, CURRENT_DATE()) as days_open,
        DATEDIFF(day, opp.created_date, opp.close_date_actual) as days_to_close,
        EXTRACT(QUARTER FROM opp.created_date) as created_quarter,
        EXTRACT(MONTH FROM opp.created_date) as created_month,
        
        -- Account Features
        acc.industry,
        acc.region,
        acc.annual_revenue_band,
        acc.account_tier,
        acc.number_of_employees,
        
        -- Activity Features
        COALESCE(act.total_activities, 0) as total_activities,
        COALESCE(act.total_meeting_minutes, 0) as total_meeting_minutes,
        COALESCE(act.total_calls, 0) as total_calls,
        COALESCE(act.total_emails, 0) as total_emails,
        COALESCE(act.days_since_last_activity, 999) as days_since_last_activity,
        
        -- Sales Rep Features
        usr.seniority_level,
        COALESCE(rep_stats.deals_handled, 0) as rep_deals_handled,
        COALESCE(rep_stats.rep_win_rate, 0) as rep_win_rate,
        
        -- Stage Features
        opp.stage,
        COALESCE(stage_hist.avg_days_in_stage, 0) as avg_days_in_stage,
        COALESCE(stage_hist.stage_changes, 0) as stage_changes,
        
        CURRENT_TIMESTAMP() as feature_created_at
    FROM sales_win_predictor.dbt_dev.fct_opportunities opp
    LEFT JOIN sales_win_predictor.dbt_dev.dim_accounts acc
        ON opp.account_id = acc.account_id
    LEFT JOIN (
        SELECT
            opportunity_id,
            COUNT(*) as total_activities,
            SUM(CASE WHEN activity_type = 'Call' THEN 1 ELSE 0 END) as total_calls,
            SUM(CASE WHEN activity_type = 'Email' THEN 1 ELSE 0 END) as total_emails,
            SUM(duration_minutes) as total_meeting_minutes,
            DATEDIFF(day, MAX(activity_date), CURRENT_DATE()) as days_since_last_activity
        FROM sales_win_predictor.dbt_dev.stg_crm_activities
        GROUP BY opportunity_id
    ) act ON opp.opportunity_id = act.opportunity_id
    LEFT JOIN (
        SELECT
            owner_user_id,
            COUNT(*) as deals_handled,
            ROUND(100.0 * SUM(is_won) / COUNT(*), 2) as rep_win_rate
        FROM sales_win_predictor.dbt_dev.fct_opportunities
        GROUP BY owner_user_id
    ) rep_stats ON opp.owner_user_id = rep_stats.owner_user_id
    LEFT JOIN sales_win_predictor.dbt_dev.dim_users usr
        ON opp.owner_user_id = usr.user_id
    LEFT JOIN (
        SELECT
            opportunity_id,
            AVG(days_in_stage) as avg_days_in_stage,
            COUNT(*) as stage_changes
        FROM sales_win_predictor.raw_crm_data.crm_opportunity_stage_history
        GROUP BY opportunity_id
    ) stage_hist ON opp.opportunity_id = stage_hist.opportunity_id
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    print(f"✓ Feature table created: fea_opportunities")

def verify_features(conn):
    """Verify features created."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sales_win_predictor.features.fea_opportunities")
    row_count = cursor.fetchone()[0]
    
    cursor.execute("""
    SELECT COUNT(*) as features_with_target
    FROM sales_win_predictor.features.fea_opportunities
    WHERE target IS NOT NULL
    """)
    target_count = cursor.fetchone()[0]
    
    print(f"✓ Total features: {row_count}")
    print(f"✓ Features with target: {target_count}")
    cursor.close()

def main():
    """Main execution."""
    print("="*60)
    print("Feature Engineering Pipeline")
    print("="*60)
    
    conn = get_snowflake_connection()
    
    try:
        create_feature_schema(conn)
        create_deal_features(conn)
        verify_features(conn)
        print("\n✓ Feature engineering complete!")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
```

### 1.2 Run Feature Creation

```bash
cd Sales-Win-Predictor
python features/create_features.py
```

Expected output:
```
============================================================
Feature Engineering Pipeline
============================================================
✓ Feature table created: fea_opportunities
✓ Total features: 50000
✓ Features with target: 45000

✓ Feature engineering complete!
```

---

## 📋 Step 2: Feature Tables Schema

### Feature Table: fea_opportunities

```
Columns:
- opportunity_id (key)
- account_id
- owner_user_id
- target (is_won: 0=lost/open, 1=won)
- amount
- discount_pct
- deal_size_category
- days_open
- days_to_close
- industry
- region
- total_activities
- total_meeting_minutes
- total_calls
- total_emails
- days_since_last_activity
- rep_seniority_level
- rep_deals_handled
- rep_win_rate
- stage
- stage_changes
```

---

## ✅ Step 3: Verify Features in Snowflake

```sql
USE DATABASE sales_win_predictor;
USE SCHEMA features;

-- Check feature table exists
SHOW TABLES;

-- View feature sample
SELECT * FROM fea_opportunities LIMIT 5;

-- Check for missing values
SELECT 
    opportunity_id,
    COUNT(*) as total_features,
    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amount,
    SUM(CASE WHEN target IS NULL THEN 1 ELSE 0 END) as null_target
FROM fea_opportunities
GROUP BY opportunity_id
HAVING COUNT(*) > 0
LIMIT 10;

-- Summary statistics
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT opportunity_id) as unique_opportunities,
    SUM(CASE WHEN target = 1 THEN 1 ELSE 0 END) as won_deals,
    SUM(CASE WHEN target = 0 THEN 1 ELSE 0 END) as lost_deals,
    ROUND(100.0 * SUM(CASE WHEN target = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct
FROM fea_opportunities;
```

---

## 🎯 Step 4: Advanced Feature Engineering (Optional)

### 4.1 Time-Series Features

Create features tracking deal momentum:

```sql
CREATE OR REPLACE TABLE fea_opportunities_timeseries AS
SELECT
    opportunity_id,
    DATEDIFF(day, created_date, CURRENT_DATE()) / 30 as months_open,
    CASE 
        WHEN DATEDIFF(day, created_date, CURRENT_DATE()) <= 30 THEN 'New'
        WHEN DATEDIFF(day, created_date, CURRENT_DATE()) <= 90 THEN 'Active'
        WHEN DATEDIFF(day, created_date, CURRENT_DATE()) <= 180 THEN 'Stale'
        ELSE 'Aged'
    END as deal_age_category,
    -- Activity trend (last 30 days)
    (SELECT COUNT(*) FROM raw_crm_data.crm_activities 
     WHERE opportunity_id = fea_opportunities.opportunity_id
     AND DATEDIFF(day, activity_date, CURRENT_DATE()) <= 30) as activities_last_30d
FROM fea_opportunities;
```

### 4.2 Interaction Features

```sql
CREATE OR REPLACE TABLE fea_opportunity_interactions AS
SELECT
    opp.opportunity_id,
    -- Account-Stage interaction
    CONCAT(opp.account_tier, '_', opp.stage) as account_stage_interaction,
    -- Rep-Size interaction
    CONCAT(opp.seniority_level, '_', opp.deal_size_category) as rep_size_interaction,
    -- Engagement-Stage interaction
    CASE 
        WHEN opp.total_activities > 10 AND opp.stage IN ('Proposal', 'Negotiation') THEN 'High_Engagement_Advanced'
        WHEN opp.total_activities <= 5 AND opp.stage = 'Prospecting' THEN 'Low_Engagement_Early'
        ELSE 'Other'
    END as engagement_stage_pattern
FROM fea_opportunities opp;
```

---

## 📊 Step 5: Export Features for ML

### 5.1 Create Training Dataset

```sql
CREATE OR REPLACE TABLE fea_training_set AS
SELECT
    *
FROM sales_win_predictor.features.fea_opportunities
WHERE target IS NOT NULL
  AND days_to_close IS NOT NULL  -- Only closed deals
  AND DATEDIFF(day, feature_created_at, CURRENT_DATE()) <= 365
ORDER BY RANDOM()
LIMIT 40000;  -- Use 40K for training
```

### 5.2 Export to CSV/Parquet

```bash
# From Python:
python -c "
import pandas as pd
import snowflake.connector

conn = snowflake.connector.connect(
    user='USERNAME',
    password='PASSWORD',
    account='ACCOUNT',
    warehouse='WH',
    database='sales_win_predictor',
    schema='features'
)

query = '''
SELECT * FROM fea_training_set
'''

df = pd.read_sql(query, conn)
df.to_parquet('ml/data/training_set.parquet', index=False)
print(f'✓ Exported {len(df)} rows to training_set.parquet')
"
```

---

## 📈 Monitoring Features

```sql
-- Check feature freshness
SELECT 
    MAX(feature_created_at) as last_refresh,
    COUNT(*) as total_records
FROM sales_win_predictor.features.fea_opportunities;

-- Check data quality
SELECT 
    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as pct_null_amount,
    SUM(CASE WHEN target IS NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as pct_null_target
FROM sales_win_predictor.features.fea_opportunities;
```

---

## 🚀 Next Steps

After feature tables are ready:

1. ✅ Proceed to [ml/](../ml/) to train ML models
2. Monitor feature freshness with `dbt freshness` command
3. Add new features as needed for model improvement

---

## 📚 Resources

- [Feature Engineering Best Practices](https://en.wikipedia.org/wiki/Feature_engineering)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference.html)
- [pandas for data manipulation](https://pandas.pydata.org/)
