# 🚀 Quick Start Guide

Get up and running with Sales Win Predictor in **10 minutes**.

---

## Prerequisites

- ✅ Snowflake account (free tier ok)
- ✅ Python 3.8+
- ✅ Git

---

## 5 Easy Steps

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/yourusername/Sales-Win-Predictor.git
cd Sales-Win-Predictor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Configure Credentials

```bash
cp .env.example .env
# Edit .env with your Snowflake account details
```

```env
SNOWFLAKE_ACCOUNT=xy12345        # Your account identifier
SNOWFLAKE_USER=your_user         # Your username
SNOWFLAKE_PASSWORD=your_pass     # Your password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH   # Or your warehouse name
```

### 3️⃣ Create Database

In Snowflake Web UI, run:

```sql
CREATE DATABASE IF NOT EXISTS sales_win_predictor;
CREATE SCHEMA IF NOT EXISTS raw_crm_data;
```

### 4️⃣ Load Data

```bash
python setup/data_ingestion.py
```

This automatically:
- Creates all 9 tables
- Uploads CSV files
- Loads data

**Progress:**
```
✓ Connected to Snowflake
✓ Database and schema ready
✓ Stage and format created
✓ Uploaded: crm_accounts.csv
✓ Uploaded: crm_activities.csv
... (more tables)
✓ ALL DATA LOADED SUCCESSFULLY
```

### 5️⃣ Verify

```sql
SELECT COUNT(*) FROM sales_win_predictor.raw_crm_data.crm_opportunities;
```

Expected: ~50,000+ opportunities loaded ✅

---

## What's Loaded?

| Table | Records | Purpose |
|-------|---------|---------|
| crm_accounts | 1,000+ | Client companies |
| crm_opportunities | 50,000+ | Sales deals |
| crm_activities | 200,000+ | Deal interactions |
| crm_contracts | 10,000+ | Won deals details |
| ... | ... | 9 tables total |

---

## Next Steps

- 📊 Explore data in Snowflake
- 🤖 Train ML models
- 📈 Build reports
- 🔄 Integrate with your CRM

---

## Troubleshooting

**Connection fails?**
- Double-check credentials in `.env`
- Verify account format: `xy12345` (not full URL)

**Data not loading?**
- Ensure CSV files exist in `Data/` folder
- Check file permissions

**Table creation errors?**
- Run `setup/sql/12_create_all_tables.sql` manually in Snowflake

---

## Need Help?

See [README.md](README.md) for detailed documentation.
