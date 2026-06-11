# 📋 Detailed Setup Guide

Complete step-by-step instructions to set up Sales Win Predictor on your local machine.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Setup Checklist](#pre-setup-checklist)
3. [Installation Steps](#installation-steps)
4. [Snowflake Configuration](#snowflake-configuration)
5. [Data Loading](#data-loading)
6. [Verification](#verification)
7. [Common Issues](#common-issues)
8. [Next Steps](#next-steps)

---

## System Requirements

### Hardware
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space
- **OS**: Windows, macOS, or Linux

### Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
  - Verify: `python --version`
- **Git** - [Download](https://git-scm.com/)
  - Verify: `git --version`
- **Snowflake Account** - [Free trial](https://signup.snowflake.com/)

### Network
- Stable internet connection
- Access to Snowflake cloud (no VPN needed for public account)

---

## Pre-Setup Checklist

Before starting, gather:

- [ ] Snowflake account identifier (e.g., `xy12345-ab67890`)
- [ ] Snowflake username
- [ ] Snowflake password
- [ ] Warehouse name (e.g., `COMPUTE_WH`)
- [ ] Warehouse running and available

**To find your Snowflake account identifier:**

1. Log in to [Snowflake Web UI](https://app.snowflake.com/)
2. Look at the URL bar: `https://<account-identifier>.snowflakecomputing.com`
3. Copy the account identifier part (not the full URL)

**To verify warehouse:**

1. In Snowflake, go to **Admin** → **Warehouses**
2. Confirm a warehouse exists and its status
3. Note the exact warehouse name

---

## Installation Steps

### Step 1: Clone Repository

```bash
# Using HTTPS (no SSH key needed)
git clone https://github.com/yourusername/Sales-Win-Predictor.git

# Navigate to project
cd Sales-Win-Predictor

# Verify you're in the right place
ls  # You should see: Data/, setup/, requirements.txt, README.md, etc.
```

### Step 2: Create Python Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verify activation:**
```bash
# You should see (venv) prefix in your terminal
which python  # macOS/Linux
where python  # Windows
```

### Step 3: Install Dependencies

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# This may take 2-5 minutes depending on internet speed
```

**Verify installation:**
```bash
python -c "import snowflake.connector; print('✓ Snowflake connector installed')"
python -c "import pandas; print('✓ Pandas installed')"
python -c "import dotenv; print('✓ Python-dotenv installed')"
```

### Step 4: Configure Environment Variables

```bash
# Copy example to create your .env file
cp .env.example .env
```

Edit `.env` with your Snowflake credentials:

```env
SNOWFLAKE_ACCOUNT=xy12345-ab67890
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=sales_win_predictor
SNOWFLAKE_SCHEMA=raw_crm_data
```

**Important:**
- Do NOT share or commit `.env` file
- It's listed in `.gitignore` for security
- Keep passwords secure

**To find warehouse name in Snowflake:**

```sql
SHOW WAREHOUSES;
```

This displays all available warehouses. Use the `name` column value.

---

## Snowflake Configuration

### Option A: Web UI (Easiest)

1. Log in to [Snowflake Web UI](https://app.snowflake.com/)

2. Click **+ Worksheets** to open new SQL editor

3. Run database setup:

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS sales_win_predictor;

-- Create schema
CREATE SCHEMA IF NOT EXISTS sales_win_predictor.raw_crm_data;

-- Verify
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE sales_win_predictor;
```

4. Highlight each statement and press **Ctrl+Enter** (or click Run)

### Option B: Command Line (SnowSQL)

1. Install SnowSQL:
   ```bash
   # See: https://docs.snowflake.com/en/user-guide/snowsql-install-config
   ```

2. Run setup script:
   ```bash
   snowsql -a <account> -u <user> -f setup/sql/01_database_schema_setup.sql
   ```

3. When prompted, enter password

---

## Data Loading

### Automated Method (Recommended)

```bash
# Make sure your .env is configured
python setup/data_ingestion.py
```

**What this script does:**
1. Connects to Snowflake
2. Creates database and schema (if needed)
3. Creates internal stage
4. Uploads 9 CSV files
5. Creates 9 tables with correct schemas
6. Loads data into each table
7. Displays row counts

**Expected output:**
```
============================================================
Sales Win Predictor - Data Ingestion
============================================================
2024-06-11 10:30:15,123 - INFO - ✓ Connected to Snowflake
2024-06-11 10:30:16,456 - INFO - Setting up database: sales_win_predictor
2024-06-11 10:30:17,789 - INFO - ✓ Database and schema ready
2024-06-11 10:30:18,012 - INFO - Creating stage: crm_stage
...
2024-06-11 10:35:00,000 - INFO - ✓ crm_opportunities: 50000 rows loaded
2024-06-11 10:35:01,234 - INFO - ============================================================
2024-06-11 10:35:01,234 - INFO - ✓ ALL DATA LOADED SUCCESSFULLY
2024-06-11 10:35:01,234 - INFO - ============================================================
```

### Manual Method

If automated method fails, run SQL scripts manually:

```bash
# Create tables
snowsql -a <account> -u <user> -f setup/sql/03_create_crm_accounts.sql
snowsql -a <account> -u <user> -f setup/sql/06_create_crm_users.sql
snowsql -a <account> -u <user> -f setup/sql/07_create_crm_products.sql
snowsql -a <account> -u <user> -f setup/sql/05_create_crm_contacts.sql
snowsql -a <account> -u <user> -f setup/sql/08_create_crm_opportunities.sql
snowsql -a <account> -u <user> -f setup/sql/04_create_crm_activities.sql
snowsql -a <account> -u <user> -f setup/sql/09_create_crm_contracts.sql
snowsql -a <account> -u <user> -f setup/sql/10_create_crm_opportunity_line_items.sql
snowsql -a <account> -u <user> -f setup/sql/11_create_crm_opportunity_stage_history.sql
```

Or use the combined script:
```bash
snowsql -a <account> -u <user> -f setup/sql/12_create_all_tables.sql
```

---

## Verification

### Verify All Tables Created

```sql
-- In Snowflake, run:
USE DATABASE sales_win_predictor;
USE SCHEMA raw_crm_data;

SHOW TABLES;
```

Expected output shows all 9 tables:
- crm_accounts
- crm_activities
- crm_contacts
- crm_contracts
- crm_opportunities
- crm_opportunity_line_items
- crm_opportunity_stage_history
- crm_products
- crm_users

### Verify Data Loaded

```sql
-- Row count for each table
SELECT 
    'crm_accounts' as table_name, 
    COUNT(*) as row_count 
FROM crm_accounts
UNION ALL
SELECT 'crm_activities', COUNT(*) FROM crm_activities
UNION ALL
SELECT 'crm_contacts', COUNT(*) FROM crm_contacts
UNION ALL
SELECT 'crm_contracts', COUNT(*) FROM crm_contracts
UNION ALL
SELECT 'crm_opportunities', COUNT(*) FROM crm_opportunities
UNION ALL
SELECT 'crm_opportunity_line_items', COUNT(*) FROM crm_opportunity_line_items
UNION ALL
SELECT 'crm_opportunity_stage_history', COUNT(*) FROM crm_opportunity_stage_history
UNION ALL
SELECT 'crm_products', COUNT(*) FROM crm_products
UNION ALL
SELECT 'crm_users', COUNT(*) FROM crm_users
ORDER BY table_name;
```

Expected row counts (approximately):
```
crm_accounts                      ~1,000
crm_activities                  ~200,000
crm_contacts                     ~5,000
crm_contracts                   ~10,000
crm_opportunities               ~50,000
crm_opportunity_line_items     ~100,000
crm_opportunity_stage_history ~200,000
crm_products                       ~100
crm_users                          ~500
```

### Spot Check Data

```sql
-- Check first few records
SELECT * FROM crm_opportunities LIMIT 5;

SELECT * FROM crm_activities LIMIT 5;

SELECT * FROM crm_accounts LIMIT 5;
```

All columns should have data, dates should be reasonable (2020-2024).

---

## Common Issues

### Issue: "Invalid Account Identifier"

**Error Message:**
```
snowflake.connector.errors.ProgrammingError: 000001 (08001): Failed to initialize pool: 
Invalid account identifier 'https://xy12345.snowflakecomputing.com'
```

**Solution:**
Account identifier should be just `xy12345`, not the full URL.

In `.env`:
```env
# ❌ Wrong
SNOWFLAKE_ACCOUNT=https://xy12345.snowflakecomputing.com

# ✅ Correct
SNOWFLAKE_ACCOUNT=xy12345
```

### Issue: "Incorrect Username or Password"

**Error Message:**
```
snowflake.connector.errors.DatabaseError: 250001 (08001): Failed to initialize pool: 
Incorrect username or password
```

**Solution:**
1. Verify credentials in `.env`
2. Try logging into Snowflake Web UI manually
3. Reset password if needed: https://app.snowflake.com/ → Account Settings
4. For complex passwords with special chars, ensure they're properly quoted in `.env`

### Issue: "No Module Named 'snowflake'"

**Error Message:**
```
ModuleNotFoundError: No module named 'snowflake'
```

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Or specifically:
pip install snowflake-connector-python
```

### Issue: "File Not Found" During Data Load

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\...\Data\crm_accounts.csv'
```

**Solution:**
1. Verify CSV files exist: `Data/` folder should contain 9 CSV files
2. Check file paths in `data_ingestion.py` match your system
3. Ensure you're running script from project root directory

### Issue: "Column Count Mismatch"

**Error Message:**
```
COPY statement error: Mismatch between number of columns
```

**Solution:**
1. Verify CSV files haven't been modified
2. Check column count in first row matches table schema
3. Ensure no trailing commas in CSV headers

### Issue: "Warehouse Does Not Exist"

**Error Message:**
```
Warehouse 'XYZ_WH' does not exist or not authorized
```

**Solution:**
1. In Snowflake Web UI, go to **Admin** → **Warehouses**
2. Find an active warehouse name
3. Update `SNOWFLAKE_WAREHOUSE` in `.env` with correct name
4. Ensure warehouse is in "Running" state

### Issue: "Permission Denied" on .env File

**Solution:**
```bash
# On Windows
icacls .env /grant %USERNAME%:F

# On macOS/Linux
chmod 600 .env
```

---

## Next Steps

After successful setup:

1. **Explore Data:**
   ```sql
   SELECT * FROM sales_win_predictor.raw_crm_data.crm_opportunities LIMIT 10;
   ```

2. **Run Analysis:**
   ```sql
   -- Win rate by sales stage
   SELECT 
       stage,
       COUNT(*) as total_deals,
       SUM(is_won) as won_deals,
       ROUND(100.0 * SUM(is_won) / COUNT(*), 2) as win_rate
   FROM crm_opportunities
   GROUP BY stage
   ORDER BY win_rate DESC;
   ```

3. **Train ML Model:**
   ```bash
   python GenerateCRMData.py
   ```

4. **Build Reports:**
   - Power BI files available in `Sales_Report.Report/`
   - Create dashboards connecting to Snowflake

5. **Contribute:**
   - Fork the repository
   - Make improvements
   - Submit pull requests

---

## Support Resources

- **Snowflake Docs**: https://docs.snowflake.com/
- **Python Docs**: https://docs.python.org/
- **Project Issues**: Create issue on GitHub
- **Snowflake Community**: https://community.snowflake.com/

---

## Summary

You should now have:
- ✅ Python environment set up
- ✅ Snowflake database and schema created
- ✅ 9 tables loaded with CRM data (~600K+ total records)
- ✅ Connection verified and working
- ✅ Ready to build ML models and analyses

**Congratulations! 🎉 Setup is complete.**

Next: Explore the data and start building your sales analytics!
