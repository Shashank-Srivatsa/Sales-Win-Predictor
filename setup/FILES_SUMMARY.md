# 📦 Open Source Setup - File Summary

This document lists all the files created to make Sales Win Predictor an open-source project.

---

## 📁 Directory Structure

```
Sales-Win-Predictor/
├── .env.example                              # Environment variables template
├── README.md                                 # Main project documentation (UPDATED)
└── setup/
    ├── QUICKSTART.md                        # 10-minute quick start guide
    ├── SETUP_GUIDE.md                       # Detailed setup instructions
    ├── data_ingestion.py                    # Automated data loading script
    └── sql/
        ├── 01_database_schema_setup.sql     # Create database & schema
        ├── 02_stage_and_format_setup.sql    # Create stage & file format
        ├── 03_create_crm_accounts.sql       # Create & load crm_accounts
        ├── 04_create_crm_activities.sql     # Create & load crm_activities
        ├── 05_create_crm_contacts.sql       # Create & load crm_contacts
        ├── 06_create_crm_users.sql          # Create & load crm_users
        ├── 07_create_crm_products.sql       # Create & load crm_products
        ├── 08_create_crm_opportunities.sql  # Create & load crm_opportunities
        ├── 09_create_crm_contracts.sql      # Create & load crm_contracts
        ├── 10_create_crm_opportunity_line_items.sql
        ├── 11_create_crm_opportunity_stage_history.sql
        └── 12_create_all_tables.sql         # Combined table creation
```

---

## 📄 File Descriptions

### Configuration Files

#### `.env.example`
- **Purpose**: Template for environment variables
- **Content**: Snowflake connection parameters (account, user, password, warehouse, database, schema)
- **Usage**: Copy to `.env` and fill with your credentials
- **Security**: Marked in `.gitignore` - never commit actual `.env`

### Documentation Files

#### `README.md` (UPDATED)
- **Purpose**: Complete project documentation for open-source users
- **Sections**:
  - Problem statement
  - Solution overview
  - Project structure
  - Prerequisites
  - Step-by-step setup instructions
  - Data dictionary
  - Troubleshooting guide
  - Contributing guidelines
  - Security best practices

#### `setup/QUICKSTART.md`
- **Purpose**: Get started in 10 minutes
- **Content**: 5 easy steps to set up the project
- **Audience**: Users wanting immediate results
- **Includes**: Verification steps and next steps

#### `setup/SETUP_GUIDE.md`
- **Purpose**: Detailed, comprehensive setup instructions
- **Sections**:
  - System requirements (hardware, software, network)
  - Pre-setup checklist
  - Step-by-step installation
  - Snowflake configuration options
  - Data loading methods
  - Verification procedures
  - Troubleshooting with solutions
  - Common error messages and fixes

### Python Scripts

#### `setup/data_ingestion.py`
- **Purpose**: Automate data loading to Snowflake
- **Features**:
  - Reads environment variables from `.env`
  - Creates Snowflake database and schema automatically
  - Creates internal stage for CSV uploads
  - Uploads all CSV files from `Data/` folder
  - Creates 9 tables with proper schemas
  - Loads data into all tables
  - Displays row counts for verification
  - Comprehensive error handling and logging
- **Usage**: `python setup/data_ingestion.py`
- **Dependencies**: snowflake-connector-python, python-dotenv

### SQL Scripts

#### `setup/sql/01_database_schema_setup.sql`
- **Purpose**: Create database and schemas
- **Includes**:
  - Create `sales_win_predictor` database
  - Create `raw_crm_data` schema (raw data)
  - Create `processed_data` schema (for transformations)
  - Create `features` schema (for ML features)
  - Verification queries

#### `setup/sql/02_stage_and_format_setup.sql`
- **Purpose**: Create Snowflake stage and file format
- **Creates**:
  - `crm_stage`: Internal stage for CSV uploads
  - `csv_format`: File format with GZIP compression, proper delimiters
  - Verification queries

#### `setup/sql/03-11_create_crm_*.sql`
- **Purpose**: Individual table creation scripts
- **Files**:
  - `03_create_crm_accounts.sql` - 1,000 client companies
  - `04_create_crm_activities.sql` - 200K+ deal interactions
  - `05_create_crm_contacts.sql` - 5K+ contact people
  - `06_create_crm_users.sql` - 500+ sales team members
  - `07_create_crm_products.sql` - 100+ products
  - `08_create_crm_opportunities.sql` - 50K+ sales deals
  - `09_create_crm_contracts.sql` - 10K+ signed contracts
  - `10_create_crm_opportunity_line_items.sql` - 100K+ line items
  - `11_create_crm_opportunity_stage_history.sql` - 200K+ stage changes

- **Each Script Includes**:
  - Table creation with proper data types
  - Column definitions and constraints
  - Comments describing purpose
  - COPY command to load data from stage
  - Verification queries (COUNT, LIMIT 5)

#### `setup/sql/12_create_all_tables.sql`
- **Purpose**: Combined script for creating all tables at once
- **Advantage**: Single file execution vs. running 9 individual scripts
- **Content**: 9 CREATE TABLE statements (without foreign keys to avoid dependency issues)
- **Usage**: `snowsql -a <account> -u <user> -f setup/sql/12_create_all_tables.sql`

---

## 📊 Data Files (In `Data/` Folder)

All CSV files are source data that gets loaded into Snowflake:

| File | Rows | Columns | Purpose |
|------|------|---------|---------|
| crm_accounts.csv | ~1,000 | 12 | Client companies |
| crm_activities.csv | ~200,000 | 10 | Sales activities (calls, emails, meetings) |
| crm_contacts.csv | ~5,000 | 11 | People at accounts |
| crm_contracts.csv | ~10,000 | 14 | Executed contracts for won deals |
| crm_opportunities.csv | ~50,000 | 22 | Sales opportunities (deals) |
| crm_opportunity_line_items.csv | ~100,000 | 13 | Products in deals |
| crm_opportunity_stage_history.csv | ~200,000 | 9 | Deal stage progression history |
| crm_products.csv | ~100 | 10 | Product catalog |
| crm_users.csv | ~500 | 12 | Sales team members |

**Total Records**: ~600,000+ across 9 tables

---

## 🚀 Setup Workflow

### For Users Starting Fresh

```
1. Clone repository
2. Read README.md (main documentation)
3. Read setup/QUICKSTART.md (10-min overview)
4. Copy .env.example to .env
5. Fill in Snowflake credentials
6. Run python setup/data_ingestion.py
7. Verify data in Snowflake
8. Start analyzing/modeling
```

### For Users Preferring Manual Control

```
1. Clone repository
2. Read setup/SETUP_GUIDE.md (detailed steps)
3. Create database using setup/sql/01_database_schema_setup.sql
4. Create stage using setup/sql/02_stage_and_format_setup.sql
5. Run individual table scripts or combined 12_create_all_tables.sql
6. Verify data with queries
```

### For Users Wanting Maximum Detail

```
1. Read README.md (full project context)
2. Read setup/SETUP_GUIDE.md (comprehensive setup)
3. Review individual SQL scripts to understand schema
4. Examine data_ingestion.py to learn automation
5. Execute step-by-step manually if desired
```

---

## ✨ Key Features of Setup

### Security
- Credentials stored in `.env` (not committed to git)
- `.env.example` shows required fields without secrets
- Snowflake role-based access control recommendations

### Automation
- `data_ingestion.py` handles all setup in one command
- Automatic table creation with proper schemas
- Data type inference and verification
- Error handling and logging

### Flexibility
- Individual SQL scripts for manual execution
- Combined script for bulk operations
- Python automation for programmatic users
- Multiple documentation paths (quick vs. detailed)

### Production-Ready
- Proper error handling in Python script
- Logging for troubleshooting
- Data type definitions for consistency
- Verification queries included
- Comment documentation in all SQL

---

## 📚 Documentation Roadmap

**For Quick Start**: `setup/QUICKSTART.md` (5 minutes)
- New users wanting fast setup
- Steps 1-5 get you running

**For Thorough Setup**: `setup/SETUP_GUIDE.md` (20-30 minutes)
- Users wanting detailed understanding
- System requirements, verification, troubleshooting
- Covers both automated and manual methods

**For Full Context**: `README.md` (30 minutes)
- Project overview and business context
- Architecture and data model
- Advanced usage and contributions
- Security best practices

**For Developers**: Source files
- `data_ingestion.py` - Learn automation patterns
- SQL scripts - Understand data schemas
- Individual table scripts - Modular examples

---

## 🔄 Maintenance & Updates

When users have new CRM data:

1. **Replace CSV files**: Put updated CSVs in `Data/` folder
2. **Re-run ingestion**: `python setup/data_ingestion.py` (idempotent - safe to re-run)
3. **Or manual SQL**: Run COPY commands again (tables use CREATE OR REPLACE)

---

## 📋 Checklist for Publishing

- [x] `.env.example` created
- [x] `README.md` updated with setup instructions
- [x] `setup/QUICKSTART.md` created for quick start
- [x] `setup/SETUP_GUIDE.md` created for detailed guidance
- [x] `setup/data_ingestion.py` created for automation
- [x] Individual SQL scripts for each table (03-11)
- [x] Combined SQL script for bulk setup (12)
- [x] Database/schema setup SQL (01-02)
- [x] All files documented with comments
- [x] Error handling and validation included
- [x] Security best practices documented

---

## 🎯 Next Steps for Users

After completing setup:

1. **Explore Data**:
   ```sql
   SELECT * FROM sales_win_predictor.raw_crm_data.crm_opportunities LIMIT 10;
   ```

2. **Analyze Patterns**:
   ```sql
   SELECT stage, COUNT(*), SUM(is_won) as wins
   FROM crm_opportunities
   GROUP BY stage;
   ```

3. **Train ML Model**:
   ```bash
   python GenerateCRMData.py
   ```

4. **Build Reports**:
   - Use Power BI models in `Sales_Report.Report/`
   - Connect to Snowflake tables

5. **Contribute**:
   - Fork repository
   - Add improvements
   - Submit pull requests

---

## 📞 Support

- Review `setup/SETUP_GUIDE.md` troubleshooting section
- Check Snowflake documentation
- Open GitHub issues for problems
- Review existing issues/discussions

---

**Last Updated**: June 2026
**Status**: Ready for open-source release
