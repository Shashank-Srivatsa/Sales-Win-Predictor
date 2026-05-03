# Sales Win Predictor — Claude Code Context File

> **Purpose:** This file is the single source of truth for Claude Code to understand the complete project.  
> It covers the business domain, Snowflake data layout, dbt modelling layers, ML pipeline, and Power BI output.  
> Read every section before generating any code.

---

## 0. Project Identity

| Item | Value |
|---|---|
| **Project name** | Sales Win Predictor |
| **Goal** | Predict probability (0–1) that an active CRM deal will be Won or Lost |
| **ML problem type** | Binary Classification |
| **Target label** | `is_won` — 1 = Won, 0 = Lost, NULL = still open |
| **Snowflake database** | `SALES_WIN_DB` |
| **Snowflake layers** | `BRONZE` → `SILVER` → `GOLD` → `ML` |
| **dbt project name** | `sales_win_predictor` |
| **ML stack** | XGBoost · SHAP · MLflow |
| **Visualisation** | Power BI (reads from `GOLD` + `ML` schemas) |

---

## 1. Business Domain

### 1.1 Company Structure

The client organisation (**GlobalTalent Group**) operates four business divisions. Every deal in the CRM belongs to exactly one division.

| Division | What They Sell | Revenue Model |
|---|---|---|
| **TalentEdge** | Models, photographers, stylists, creative directors | Agent commission on day-rate bookings |
| **CreativeMotion** | Scriptwriters, directors, designers, content writers | Fixed project fee + talent placement |
| **PulseMedia** | Marketing campaigns, digital, branding, social | Billable hours by seniority OR fixed fee |
| **BrandVault** | Brand / trademark licensing (logos, characters) | Minimum Guarantee (MG) + Royalty % |

### 1.2 CRM Deal Lifecycle

Every revenue opportunity goes through a five-stage funnel:

```
Lead → Qualified Lead → Opportunity → Negotiation → Closed Won / Closed Lost
```

- **Deal Funnel** (conversion view): what % of deals survive each stage transition
- **Deal Pipeline** (forecast view): total value of all currently active deals

### 1.3 What a Deal Is Made Of

Every deal (`crm_opportunities`) has:
- One **account** (the client brand)
- One **owner** (the internal agent)
- Multiple **line items** (individual billable services/talents)
- A trail of **stage transitions** (how long it spent at each stage)
- A log of **activities** (emails, calls, meetings)
- A **contract** record if it was won

### 1.4 Key Business Rules

- Renewals (`is_renewal = 1`) win at roughly 2× the rate of new business
- Discounts above 20% are a strong negative signal
- Agents managing more than 30 simultaneous deals have lower win rates
- Deals stalled in Negotiation for more than 21 days frequently result in loss
- BrandVault deals are hardest to close; PulseMedia closes most reliably
- Quarter-end months (March, June, September, December) have higher close rates

---

## 2. Snowflake Setup

### 2.1 Connection Details

```
Database   : SALES_WIN_DB
Warehouse  : COMPUTE_WH
Schemas    : BRONZE  /  SILVER  /  GOLD  /  ML
```

> **Never hard-code credentials in dbt or Python files.**  
> Use `profiles.yml` for dbt and environment variables for Python.

### 2.2 dbt profiles.yml (reference)

```yaml
sales_win_predictor:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: SYSADMIN
      database: SALES_WIN_DB
      warehouse: COMPUTE_WH
      schema: SILVER
      threads: 4
```

---

## 3. Bronze Layer — Source Tables

These are the **raw CRM tables** loaded from CSV into `SALES_WIN_DB.BRONZE`.  
They are flat, operational, and have **no star schema**.  
**Never modify Bronze tables** — they are the immutable source of truth.

### 3.1 Table Inventory

| Table Name | Rows (approx.) | Description |
|---|---|---|
| `CRM_ACCOUNTS` | 210 | Client brand companies |
| `CRM_CONTACTS` | 510 | People at those companies |
| `CRM_USERS` | 82 | Internal agents and employees |
| `CRM_OPPORTUNITIES` | 1,850 | **The main deals table** |
| `CRM_OPPORTUNITY_LINE_ITEMS` | ~8,000 | Individual billable items per deal |
| `CRM_OPPORTUNITY_STAGE_HISTORY` | ~9,500 | Every stage transition per deal |
| `CRM_ACTIVITIES` | ~13,000 | Emails, calls, meetings per deal |
| `CRM_CONTRACTS` | ~750 | Contracts for won deals only |
| `CRM_PRODUCTS` | 48 | Service and talent product catalogue |

### 3.2 Column Definitions — CRM_ACCOUNTS

| Column | Type | Description |
|---|---|---|
| `account_id` | VARCHAR | Unique CRM ID (e.g. `ACC-1000`) |
| `account_name` | VARCHAR | Name of the brand/company |
| `industry` | VARCHAR | Sector (Fashion, Sportswear, Entertainment, etc.) |
| `country` | VARCHAR | HQ country |
| `region` | VARCHAR | Sales region: North America, Europe, India, Asia Pacific, Australia |
| `annual_revenue_band` | VARCHAR | Revenue bracket: `<$10M`, `$10M–$100M`, `$100M–$500M`, `$500M–$1B`, `>$1B` |
| `account_type` | VARCHAR | `Prospect` or `Customer` |
| `account_tier` | NUMBER | 1 = top client, 2 = mid, 3 = small/new |
| `number_of_employees` | NUMBER | Approximate headcount |
| `is_active` | NUMBER | 1 = active, 0 = inactive/churned |
| `created_date` | DATE | When first added to CRM |

### 3.3 Column Definitions — CRM_CONTACTS

| Column | Type | Description |
|---|---|---|
| `contact_id` | VARCHAR | Unique ID (e.g. `CON-2000`) |
| `account_id` | VARCHAR | FK → `CRM_ACCOUNTS` |
| `first_name` | VARCHAR | First name |
| `last_name` | VARCHAR | Last name |
| `email` | VARCHAR | Work email |
| `job_title` | VARCHAR | Role (CMO, VP Marketing, Brand Manager, etc.) |
| `department` | VARCHAR | Marketing / Brand / Procurement / Creative / Commercial / Licensing |
| `is_primary_contact` | NUMBER | 1 = main point of contact |
| `is_decision_maker` | NUMBER | 1 = holds budget authority |
| `created_date` | DATE | Added to CRM |
| `is_active` | NUMBER | 1 = still reachable |

### 3.4 Column Definitions — CRM_USERS

| Column | Type | Description |
|---|---|---|
| `user_id` | VARCHAR | Unique agent ID (e.g. `USR-3000`) |
| `first_name` | VARCHAR | First name |
| `last_name` | VARCHAR | Last name |
| `email` | VARCHAR | Internal email |
| `role` | VARCHAR | Job title (Junior Agent, Senior Account Manager, etc.) |
| `division` | VARCHAR | Which division: TalentEdge / CreativeMotion / PulseMedia / BrandVault / Management |
| `region` | VARCHAR | Primary operating region |
| `seniority_level` | NUMBER | 1=Junior, 2=Mid, 3=Senior, 4=Director, 5=VP/Head |
| `hire_date` | DATE | When they joined |
| `is_active` | NUMBER | 1 = still employed |
| `manager_id` | VARCHAR | FK → `CRM_USERS` (their manager) |
| `target_deals_per_year` | NUMBER | Annual new deal target |

### 3.5 Column Definitions — CRM_OPPORTUNITIES ⭐ MAIN TABLE

| Column | Type | Description |
|---|---|---|
| `opportunity_id` | VARCHAR | Unique deal ID (e.g. `OPP-4000`) |
| `opportunity_name` | VARCHAR | Human-readable name |
| `account_id` | VARCHAR | FK → `CRM_ACCOUNTS` |
| `primary_contact_id` | VARCHAR | FK → `CRM_CONTACTS` |
| `owner_user_id` | VARCHAR | FK → `CRM_USERS` (assigned agent) |
| `division` | VARCHAR | TalentEdge / CreativeMotion / PulseMedia / BrandVault |
| `region` | VARCHAR | Geographic region |
| `deal_type` | VARCHAR | New Business / Renewal / Upsell / Cross-sell |
| `lead_source` | VARCHAR | Inbound Inquiry / Referral / Outbound / Conference / etc. |
| `stage` | VARCHAR | Current CRM stage at export time |
| `amount` | FLOAT | Total deal value in USD |
| `discount_pct` | FLOAT | Discount % offered to the client |
| `probability_manual` | NUMBER | Agent's gut-feel win % typed into CRM — NOT the ML prediction |
| `created_date` | DATE | When deal was first logged |
| `expected_close_date` | DATE | Target close date set at creation |
| `close_date_actual` | DATE | When it actually closed (NULL if open) |
| `is_won` | NUMBER | **1 = Won, 0 = Lost, NULL = still open — THE ML TARGET** |
| `lost_reason` | VARCHAR | Why it was lost (NULL if won or open) |
| `is_renewal` | NUMBER | 1 = renewal deal |
| `fiscal_year` | NUMBER | Year created |
| `fiscal_quarter` | VARCHAR | Q1 / Q2 / Q3 / Q4 |
| `is_open` | NUMBER | 1 = still active |

### 3.6 Column Definitions — CRM_OPPORTUNITY_LINE_ITEMS

| Column | Type | Description |
|---|---|---|
| `line_item_id` | VARCHAR | Unique ID (e.g. `LI-5000`) |
| `opportunity_id` | VARCHAR | FK → `CRM_OPPORTUNITIES` |
| `product_id` | VARCHAR | FK → `CRM_PRODUCTS` |
| `line_item_name` | VARCHAR | Service name (e.g. `Model - Day Rate`) |
| `line_item_type` | VARCHAR | Category: Talent Day Rate / Usage Rights / Billable Hours / Licensing MG / etc. |
| `unit_type` | VARCHAR | `per day` / `per hour` / `per month` / `flat fee` |
| `unit_price` | FLOAT | Price per unit |
| `quantity` | NUMBER | Units (days, hours, months, or 1 for flat) |
| `gross_amount` | FLOAT | `unit_price × quantity` before discount |
| `discount_applied_pct` | FLOAT | Discount % on this specific line item |
| `net_amount` | FLOAT | Amount after discount — what the client pays |
| `is_negotiated` | NUMBER | 1 = price negotiated below catalogue rate |
| `created_date` | DATE | When added to the deal |

### 3.7 Column Definitions — CRM_OPPORTUNITY_STAGE_HISTORY

| Column | Type | Description |
|---|---|---|
| `stage_history_id` | VARCHAR | Unique ID (e.g. `SH-6000`) |
| `opportunity_id` | VARCHAR | FK → `CRM_OPPORTUNITIES` |
| `from_stage` | VARCHAR | Previous stage (NULL for first entry) |
| `to_stage` | VARCHAR | Stage moved into |
| `stage_entered_date` | DATE | Date entered this stage |
| `stage_exited_date` | DATE | Date left this stage (NULL = current stage) |
| `days_in_stage` | NUMBER | Days spent in this stage |
| `changed_by_user_id` | VARCHAR | FK → `CRM_USERS` |
| `is_regression` | NUMBER | 1 = deal moved backwards in the funnel |

### 3.8 Column Definitions — CRM_ACTIVITIES

| Column | Type | Description |
|---|---|---|
| `activity_id` | VARCHAR | Unique ID (e.g. `ACT-7000`) |
| `opportunity_id` | VARCHAR | FK → `CRM_OPPORTUNITIES` |
| `user_id` | VARCHAR | FK → `CRM_USERS` |
| `activity_type` | VARCHAR | Email / Phone Call / Video Meeting / In-Person Meeting / Demo / Proposal Sent |
| `subject` | VARCHAR | Brief description |
| `activity_date` | DATE | When it happened |
| `duration_minutes` | NUMBER | Length in minutes (NULL for emails) |
| `outcome` | VARCHAR | Positive / Neutral / Negative classification |
| `is_outbound` | NUMBER | 1 = agent contacted client, 0 = client reached out |
| `days_since_deal_created` | NUMBER | Days into the deal lifecycle |

### 3.9 Column Definitions — CRM_CONTRACTS

| Column | Type | Description |
|---|---|---|
| `contract_id` | VARCHAR | Unique ID (e.g. `CON-8000`) |
| `opportunity_id` | VARCHAR | FK → `CRM_OPPORTUNITIES` |
| `account_id` | VARCHAR | FK → `CRM_ACCOUNTS` |
| `contract_start_date` | DATE | When contract becomes active |
| `contract_end_date` | DATE | When it expires |
| `contract_duration_months` | NUMBER | Length in months (6/12/18/24/36) |
| `contract_value` | FLOAT | Total agreed value = deal amount |
| `payment_terms` | VARCHAR | Net 30 / Net 60 / 50% upfront / Monthly / Upon signing |
| `signed_date` | DATE | Counter-signed by both parties |
| `contract_status` | VARCHAR | Active / Expired / Renewed / Cancelled |
| `has_royalty_clause` | NUMBER | 1 = BrandVault deal with royalty % |
| `royalty_pct` | FLOAT | % of net sales above threshold (BrandVault only, else NULL) |
| `royalty_threshold_usd` | FLOAT | Sales level above which royalty kicks in (else NULL) |
| `number_of_revisions` | NUMBER | Times contract was redrafted before signing |

### 3.10 Column Definitions — CRM_PRODUCTS

| Column | Type | Description |
|---|---|---|
| `product_id` | VARCHAR | Unique catalogue ID (e.g. `PRD-9000`) |
| `product_name` | VARCHAR | Service name |
| `product_category` | VARCHAR | High-level category |
| `division` | VARCHAR | Which division offers this |
| `standard_unit_price` | FLOAT | Catalogue base price (mid-point, pre-negotiation) |
| `unit_type` | VARCHAR | per day / per hour / per month / flat fee |
| `price_range_low` | NUMBER | Minimum realistic price |
| `price_range_high` | NUMBER | Maximum realistic price |
| `is_active` | NUMBER | 1 = still in catalogue |
| `catalogue_added_date` | DATE | When added |

---

## 4. dbt Project Structure

### 4.1 Folder Layout

```
sales_win_predictor/
├── dbt_project.yml
├── profiles.yml             # local only — never commit
├── packages.yml             # dbt_utils
├── models/
│   ├── staging/             # Bronze → Silver  (stg_ prefix)
│   │   ├── sources.yml
│   │   ├── schema.yml
│   │   ├── stg_crm_accounts.sql
│   │   ├── stg_crm_contacts.sql
│   │   ├── stg_crm_users.sql
│   │   ├── stg_crm_opportunities.sql
│   │   ├── stg_crm_line_items.sql
│   │   ├── stg_crm_stage_history.sql
│   │   ├── stg_crm_activities.sql
│   │   ├── stg_crm_contracts.sql
│   │   └── stg_crm_products.sql
│   ├── intermediate/        # Cross-table logic  (int_ prefix)
│   │   ├── schema.yml
│   │   ├── int_agent_performance.sql
│   │   ├── int_client_deal_history.sql
│   │   ├── int_deal_activity_summary.sql
│   │   └── int_deal_line_item_summary.sql
│   ├── mart/                # Gold Star Schema  (dim_ / fact_ prefix)
│   │   ├── schema.yml
│   │   ├── dim_account.sql
│   │   ├── dim_user.sql
│   │   ├── dim_date.sql
│   │   ├── fact_opportunities.sql
│   │   ├── fact_line_items.sql
│   │   └── fact_stage_history.sql
│   └── ml/                  # ML feature table
│       ├── schema.yml
│       └── ml_deal_features.sql
├── tests/
│   └── generic/
├── macros/
│   ├── fiscal_quarter_end.sql
│   └── safe_divide.sql
└── seeds/
    └── region_config.csv
```

### 4.2 dbt_project.yml

```yaml
name: 'sales_win_predictor'
version: '1.0.0'
config-version: 2

profile: 'sales_win_predictor'

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
macro-paths: ["macros"]

models:
  sales_win_predictor:
    staging:
      +schema: SILVER
      +materialized: view
    intermediate:
      +schema: SILVER
      +materialized: view
    mart:
      +schema: GOLD
      +materialized: table
    ml:
      +schema: ML
      +materialized: table
```

### 4.3 sources.yml (in staging/)

```yaml
version: 2

sources:
  - name: bronze
    database: SALES_WIN_DB
    schema: BRONZE
    tables:
      - name: CRM_ACCOUNTS
      - name: CRM_CONTACTS
      - name: CRM_USERS
      - name: CRM_OPPORTUNITIES
      - name: CRM_OPPORTUNITY_LINE_ITEMS
      - name: CRM_OPPORTUNITY_STAGE_HISTORY
      - name: CRM_ACTIVITIES
      - name: CRM_CONTRACTS
      - name: CRM_PRODUCTS
```

---

## 5. Silver Layer — Staging Models

### 5.1 Staging Rules (apply to every stg_ model)

1. Reference source tables via `{{ source('bronze', 'TABLE_NAME') }}`
2. Deduplicate using `ROW_NUMBER() OVER (PARTITION BY primary_key ORDER BY ... DESC)`
3. Cast all columns to correct types (`::VARCHAR`, `::FLOAT`, `::DATE`, `::INT`)
4. Standardise string values — `TRIM(UPPER(...))` for categorical columns
5. Replace NULLs with business-appropriate defaults using `COALESCE`
6. Add a `_loaded_at` metadata column: `CURRENT_TIMESTAMP AS _loaded_at`
7. Never add business logic — pure cleaning only

### 5.2 stg_crm_opportunities.sql (most important)

Key transformations required:
- Deduplicate on `opportunity_id`
- Normalise `division` to exactly: `TalentEdge`, `CreativeMotion`, `PulseMedia`, `BrandVault`
- Cast `amount` and `discount_pct` to FLOAT
- Cast all date columns to DATE type using `TRY_TO_DATE`
- Keep `is_won` as-is (NULL for open deals — do NOT fill with 0)
- Add: `total_days_in_funnel = DATEDIFF('day', created_date, COALESCE(close_date_actual, CURRENT_DATE))`
- Add: `days_overdue = DATEDIFF('day', expected_close_date, CURRENT_DATE)` (positive = overdue)

### 5.3 stg_crm_stage_history.sql

Key transformations required:
- Deduplicate on `stage_history_id`
- Compute `days_in_stage` where NULL: `DATEDIFF('day', stage_entered_date, COALESCE(stage_exited_date, CURRENT_DATE))`
- Add `stage_order` mapping:
  - Lead = 1, Qualified Lead = 2, Opportunity = 3, Negotiation = 4, Closed Won = 5, Closed Lost = 5

### 5.4 stg_crm_activities.sql

Key transformations required:
- Add `is_positive_outcome = CASE WHEN outcome ILIKE '%Positive%' THEN 1 ELSE 0 END`
- Add `is_negative_outcome = CASE WHEN outcome ILIKE '%Negative%' THEN 1 ELSE 0 END`

---

## 6. Silver Layer — Intermediate Models

### 6.1 int_agent_performance.sql

**Purpose:** Compute rolling performance metrics per agent.  
**Output:** One row per agent.

Columns to compute:
```sql
-- For each agent, looking at CLOSED deals only:
agent_id,
total_closed_deals,
total_won_deals,
overall_win_rate,                     -- won / closed
trailing_12m_closed_deals,            -- closed in last 12 months
trailing_12m_won_deals,
trailing_12m_win_rate,                -- KEY FEATURE
avg_deal_value_won,                   -- avg amount on won deals
avg_days_to_close_won,                -- avg total_days_in_funnel on won deals
current_open_deals,                   -- count of open deals right now
-- Win rate by division (one row per agent, separate columns)
win_rate_talengedge,
win_rate_creativemotion,
win_rate_pulsemedia,
win_rate_brandvault
```

### 6.2 int_client_deal_history.sql

**Purpose:** Compute client-level history for every account.  
**Output:** One row per account.

Columns to compute:
```sql
account_id,
total_deals_ever,
total_won_deals,
client_win_rate,                      -- KEY FEATURE
client_is_new,                        -- 1 if no prior won deals
total_lifetime_value,                 -- sum of won deal amounts
avg_deal_value,
days_since_last_closed_deal,          -- KEY FEATURE
total_active_deals,                   -- open deals right now
most_common_division,
client_preferred_region
```

### 6.3 int_deal_activity_summary.sql

**Purpose:** Aggregate activity metrics per deal.  
**Output:** One row per opportunity.

Columns to compute:
```sql
opportunity_id,
total_activities,
total_positive_activities,
total_negative_activities,
positive_activity_ratio,              -- positive / total
last_activity_date,
days_since_last_activity,             -- KEY FEATURE (silence = disengagement)
activities_last_14_days,
engagement_score,                     -- activities_last_14 / total (recency-weighted)
total_meetings,
total_calls,
total_emails
```

### 6.4 int_deal_line_item_summary.sql

**Purpose:** Aggregate line item metrics per deal.  
**Output:** One row per opportunity.

Columns to compute:
```sql
opportunity_id,
line_item_count,                      -- KEY FEATURE
distinct_line_item_types,
deal_complexity_score,                -- line_item_count * distinct_types
total_gross_amount,
total_net_amount,
max_line_item_discount,
avg_line_item_discount,
has_usage_rights,                     -- 1 if any Usage Rights line item
has_minimum_guarantee,                -- 1 if any MG line item (BrandVault)
negotiated_item_count                 -- count of is_negotiated = 1
```

---

## 7. Gold Layer — Mart Models

### 7.1 dim_account.sql

One row per account. Joins `stg_crm_accounts` + `int_client_deal_history`.

Key columns: `account_id`, `account_name`, `industry`, `region`, `account_tier`,  
`client_win_rate`, `client_is_new`, `total_lifetime_value`, `days_since_last_closed_deal`

### 7.2 dim_user.sql

One row per user. Joins `stg_crm_users` + `int_agent_performance`.

Key columns: `user_id`, `full_name`, `division`, `region`, `seniority_level`,  
`trailing_12m_win_rate`, `current_open_deals`, `avg_days_to_close_won`

### 7.3 dim_date.sql

Standard date spine from `2015-01-01` to `2025-12-31`.

Required columns:
```sql
date_day,
year, quarter, month, month_name, week_of_year, day_of_week,
is_weekend,
is_fiscal_quarter_end,   -- TRUE for last 14 days of March, June, Sept, Dec
is_month_end,
fiscal_year, fiscal_quarter_label   -- e.g. 'FY2023-Q4'
```

### 7.4 fact_opportunities.sql

**Core business fact table.** One row per opportunity.

Joins:
- `stg_crm_opportunities` (base)
- `int_agent_performance` (agent metrics at time of snapshot)
- `int_client_deal_history` (client history)
- `int_deal_activity_summary` (engagement metrics)
- `int_deal_line_item_summary` (complexity metrics)
- `stg_crm_stage_history` (days in each stage via pivot/conditional aggregation)

All columns from `stg_crm_opportunities` PLUS:

```sql
-- Agent features
agent_trailing_12m_win_rate,
agent_seniority_level,
agent_current_open_deals,
agent_win_rate_this_division,       -- win rate in the SAME division as this deal
is_vertical_specialist,             -- 1 if agent.division = opportunity.division

-- Client features
client_win_rate,
client_is_new,
client_total_lifetime_value,
client_days_since_last_deal,

-- Activity features
total_activities,
days_since_last_activity,
engagement_score,
positive_activity_ratio,

-- Line item features
line_item_count,
deal_complexity_score,
has_usage_rights,
has_minimum_guarantee,

-- Stage timing features
days_in_lead_stage,
days_in_qualified_stage,
days_in_opportunity_stage,
days_in_negotiation_stage,          -- KEY FEATURE
total_days_in_funnel,
stage_regression_count,

-- Time context
is_fiscal_quarter_end_period,       -- 1 if created in last 14 days of quarter
days_until_expected_close,
is_overdue
```

### 7.5 fact_line_items.sql

One row per line item. Joins `stg_crm_line_items` + `stg_crm_products` + `fact_opportunities`.

### 7.6 fact_stage_history.sql

One row per stage transition. All columns from `stg_crm_stage_history` plus `opportunity_name`, `division`, `is_won`.

---

## 8. ML Layer — Feature Table

### 8.1 ml_deal_features.sql

**Purpose:** Final feature table for XGBoost training and inference.  
**Materialization:** `table` in `ML` schema.  
**Grain:** One row per closed deal (for training) OR per open deal (for scoring).

**Critical rule — No Data Leakage:**
> Only include features that would be known at the point of entering the Negotiation stage.
> Never include: `close_date_actual`, post-negotiation `amount` changes, `contract_*` columns.

```sql
-- Source: fact_opportunities filtered at Negotiation snapshot
-- For training: WHERE is_won IS NOT NULL
-- For scoring:  WHERE is_open = 1

SELECT
    -- Identifiers (not used as model features — kept for joining)
    opportunity_id,
    account_id,
    owner_user_id,

    -- TARGET (NULL for open/scoring rows)
    is_won                                          AS target,

    -- ── DEAL FEATURES ──────────────────────────────────────────────────
    LN(amount + 1)                                  AS deal_value_log,
    amount                                          AS deal_value_raw,
    discount_pct,
    CASE
        WHEN discount_pct < 10  THEN 0.0
        WHEN discount_pct < 20  THEN 0.2
        WHEN discount_pct < 30  THEN 0.6
        ELSE                         1.0
    END                                             AS discount_risk_score,
    is_renewal,
    CASE deal_type
        WHEN 'New Business' THEN 0
        WHEN 'Renewal'      THEN 1
        WHEN 'Upsell'       THEN 2
        WHEN 'Cross-sell'   THEN 3
    END                                             AS deal_type_encoded,
    CASE division
        WHEN 'TalentEdge'    THEN 0
        WHEN 'CreativeMotion' THEN 1
        WHEN 'PulseMedia'    THEN 2
        WHEN 'BrandVault'    THEN 3
    END                                             AS division_encoded,
    CASE region
        WHEN 'North America' THEN 0
        WHEN 'Europe'        THEN 1
        WHEN 'India'         THEN 2
        WHEN 'Asia Pacific'  THEN 3
        WHEN 'Australia'     THEN 4
    END                                             AS region_encoded,

    -- ── DEAL TIMING FEATURES ───────────────────────────────────────────
    total_days_in_funnel,
    days_in_negotiation_stage,
    days_in_opportunity_stage,
    is_fiscal_quarter_end_period,
    EXTRACT(MONTH FROM created_date)                AS created_month,
    EXTRACT(YEAR FROM created_date)                 AS created_year,

    -- ── DEAL COMPLEXITY FEATURES ───────────────────────────────────────
    line_item_count,
    deal_complexity_score,
    has_usage_rights,
    has_minimum_guarantee,

    -- ── VELOCITY SCORE ─────────────────────────────────────────────────
    -- How fast is this deal moving vs historical median for same division?
    -- Computed as: expected_median_days / actual_days_in_funnel
    -- Built in a CTE using historical medians per division
    deal_velocity_score,

    -- ── AGENT FEATURES ─────────────────────────────────────────────────
    agent_trailing_12m_win_rate,
    agent_seniority_level,
    agent_current_open_deals,
    agent_win_rate_this_division,
    is_vertical_specialist,

    -- ── CLIENT FEATURES ────────────────────────────────────────────────
    client_win_rate,
    client_is_new,
    client_days_since_last_deal,
    account_tier,

    -- ── ENGAGEMENT FEATURES ────────────────────────────────────────────
    total_activities,
    days_since_last_activity,
    engagement_score,
    positive_activity_ratio,

    -- ── NEGOTIATION FLAGS ──────────────────────────────────────────────
    stage_regression_count,
    COALESCE(contract_revision_count, 0)            AS contract_revision_count,

    -- Metadata
    created_date,
    fiscal_year,
    fiscal_quarter

FROM {{ ref('fact_opportunities') }} fo
LEFT JOIN (
    -- Compute deal_velocity_score
    SELECT
        opportunity_id,
        CASE
            WHEN total_days_in_funnel > 0
            THEN div_median_days / NULLIF(total_days_in_funnel, 0)
            ELSE 1.0
        END AS deal_velocity_score
    FROM {{ ref('fact_opportunities') }}
    JOIN (
        SELECT division,
               MEDIAN(total_days_in_funnel) AS div_median_days
        FROM {{ ref('fact_opportunities') }}
        WHERE is_won IS NOT NULL
        GROUP BY division
    ) medians USING (division)
) vel USING (opportunity_id)
LEFT JOIN (
    SELECT opportunity_id,
           number_of_revisions AS contract_revision_count
    FROM {{ ref('fact_opportunities') }}
    -- contracts only exist for won deals; for others this is NULL → COALESCE to 0
) cr USING (opportunity_id)
```

### 8.2 Required dbt Tests for ml_deal_features

```yaml
models:
  - name: ml_deal_features
    columns:
      - name: opportunity_id
        tests: [unique, not_null]
      - name: target
        tests:
          - accepted_values:
              values: [0, 1]    # NULL is allowed for open deals
      - name: deal_value_log
        tests: [not_null]
      - name: discount_pct
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100
      - name: agent_trailing_12m_win_rate
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1
```

---

## 9. ML Pipeline — Python

### 9.1 File Structure

```
ml/
├── config.py               # Snowflake connection + feature list constants
├── 01_eda.py               # Exploratory Data Analysis
├── 02_train.py             # XGBoost training with MLflow
├── 03_evaluate.py          # Threshold optimisation + business metrics
├── 04_explain.py           # SHAP analysis
├── 05_score.py             # Batch scoring of open deals
├── 06_write_predictions.py # Write predictions back to Snowflake
└── requirements.txt
```

### 9.2 requirements.txt

```
snowflake-connector-python[pandas]
pandas
numpy
scikit-learn
xgboost
shap
imbalanced-learn
mlflow
matplotlib
seaborn
python-dotenv
```

### 9.3 config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_CONFIG = {
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": "COMPUTE_WH",
    "database":  "SALES_WIN_DB",
    "schema":    "ML",
}

MLFLOW_TRACKING_URI = "mlflow_runs"   # local folder
EXPERIMENT_NAME     = "sales_win_predictor"
MODEL_NAME          = "xgboost_win_predictor"

# All feature columns fed to XGBoost
# Identifiers (opportunity_id etc.) are EXCLUDED from this list
FEATURE_COLS = [
    "deal_value_log", "discount_pct", "discount_risk_score",
    "is_renewal", "deal_type_encoded", "division_encoded", "region_encoded",
    "total_days_in_funnel", "days_in_negotiation_stage", "days_in_opportunity_stage",
    "is_fiscal_quarter_end_period", "created_month",
    "line_item_count", "deal_complexity_score", "has_usage_rights", "has_minimum_guarantee",
    "deal_velocity_score",
    "agent_trailing_12m_win_rate", "agent_seniority_level",
    "agent_current_open_deals", "agent_win_rate_this_division", "is_vertical_specialist",
    "client_win_rate", "client_is_new", "client_days_since_last_deal", "account_tier",
    "total_activities", "days_since_last_activity", "engagement_score",
    "positive_activity_ratio", "stage_regression_count", "contract_revision_count",
]

TARGET_COL  = "target"
ID_COL      = "opportunity_id"

# Business decision threshold (tuned on Precision-Recall curve)
# Lower than 0.5 because False Negatives cost ~50x more than False Positives
DECISION_THRESHOLD = 0.38
```

### 9.4 02_train.py — Core Training Script

```python
"""
Train XGBoost model for Sales Win Predictor.
Uses: SMOTE for class imbalance, MLflow for experiment tracking.
Uses CHRONOLOGICAL train/test split — never random.
"""
import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
import xgboost as xgb
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report, f1_score
from sklearn.model_selection import RandomizedSearchCV
from imblearn.over_sampling import SMOTE
import snowflake.connector
from config import SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL, EXPERIMENT_NAME, MODEL_NAME

# ── Load training data from Snowflake ────────────────────────────────────────
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df   = pd.read_sql(
    "SELECT * FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES WHERE TARGET IS NOT NULL",
    conn
)
conn.close()

# ── Chronological train/test split ───────────────────────────────────────────
# NEVER use random split for time-series deal data
train = df[df["FISCAL_YEAR"] <= 2022]
test  = df[df["FISCAL_YEAR"] >= 2023]

X_train = train[FEATURE_COLS].copy()
y_train = train[TARGET_COL].astype(int)
X_test  = test[FEATURE_COLS].copy()
y_test  = test[TARGET_COL].astype(int)

# ── Apply SMOTE to training data ONLY ────────────────────────────────────────
sm = SMOTE(random_state=42)
X_train_sm, y_train_sm = sm.fit_resample(X_train, y_train)

# ── MLflow experiment ────────────────────────────────────────────────────────
mlflow.set_tracking_uri("mlflow_runs")
mlflow.set_experiment(EXPERIMENT_NAME)

neg_count = (y_train == 0).sum()
pos_count = (y_train == 1).sum()
scale_pos = neg_count / pos_count

with mlflow.start_run(run_name="xgboost_v1"):
    model = xgb.XGBClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )
    model.fit(
        X_train_sm, y_train_sm,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.38).astype(int)   # business threshold

    auc = roc_auc_score(y_test, proba)
    f1  = f1_score(y_test, preds)

    mlflow.log_param("n_estimators",   400)
    mlflow.log_param("learning_rate",  0.05)
    mlflow.log_param("threshold",      0.38)
    mlflow.log_metric("roc_auc",       auc)
    mlflow.log_metric("f1_won",        f1)
    mlflow.xgboost.log_model(model, MODEL_NAME,
                              registered_model_name=MODEL_NAME)

    print(f"ROC-AUC : {auc:.4f}  (target > 0.80)")
    print(f"F1-Won  : {f1:.4f}  (target > 0.68)")
    print(classification_report(y_test, preds, target_names=["Lost","Won"]))
```

### 9.5 04_explain.py — SHAP

```python
"""
Generate SHAP explanations.
Produces: global feature importance, per-deal top factors.
"""
import shap, mlflow, pandas as pd, matplotlib.pyplot as plt
from config import SNOWFLAKE_CONFIG, FEATURE_COLS, MODEL_NAME

# Load model from MLflow registry
model = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/Production")

# Load test data
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
X_test = pd.read_sql(
    "SELECT * FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES WHERE FISCAL_YEAR >= 2023 AND TARGET IS NOT NULL",
    conn
)[FEATURE_COLS]
conn.close()

explainer   = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# ── Global plot ──────────────────────────────────────────────────────────────
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig("shap_global_importance.png", dpi=150)

# ── Per-deal top factors (for writing back to Snowflake) ─────────────────────
def top_shap_factors(shap_vals, feature_names, n=3):
    """Return top n positive and negative SHAP feature names as strings."""
    idx_sorted = abs(shap_vals).argsort()[::-1]
    pos = [feature_names[i] for i in idx_sorted if shap_vals[i] > 0][:n]
    neg = [feature_names[i] for i in idx_sorted if shap_vals[i] < 0][:n]
    return ", ".join(pos), ", ".join(neg)
```

### 9.6 06_write_predictions.py — Write Back to Snowflake

Writes predictions to: `SALES_WIN_DB.ML.ML_PREDICTIONS`

```sql
-- Table to create in Snowflake before running this script:
CREATE OR REPLACE TABLE SALES_WIN_DB.ML.ML_PREDICTIONS (
    opportunity_id          VARCHAR,
    prediction_date         DATE,
    model_version           VARCHAR,
    win_probability         FLOAT,
    win_predicted           BOOLEAN,
    probability_band        VARCHAR,    -- HIGH / MEDIUM / LOW
    top_positive_factors    VARCHAR,    -- comma-separated SHAP feature names
    top_negative_factors    VARCHAR,
    scored_at               TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
);
```

Python write-back pattern:
```python
# After computing predictions + SHAP for all open deals:
results_df["probability_band"] = pd.cut(
    results_df["win_probability"],
    bins=[0, 0.40, 0.70, 1.01],
    labels=["LOW", "MEDIUM", "HIGH"]
)

# Use write_pandas from snowflake-connector-python
from snowflake.connector.pandas_tools import write_pandas
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
write_pandas(conn, results_df, "ML_PREDICTIONS",
             database="SALES_WIN_DB", schema="ML",
             overwrite=False)   # append daily
conn.close()
```

---

## 10. Power BI — Dashboard Requirements

### 10.1 Snowflake Tables to Import

| Table | Schema | Purpose |
|---|---|---|
| `fact_opportunities` | GOLD | All deal details + feature columns |
| `dim_account` | GOLD | Client attributes |
| `dim_user` | GOLD | Agent attributes + win rates |
| `dim_date` | GOLD | Date dimension — **mark as Date Table** |
| `fact_stage_history` | GOLD | Funnel analysis |
| `ml_deal_features` | ML | Feature values for analysis |
| `ML_PREDICTIONS` | ML | Win probability scores |

Use **Import mode** for v1. Schedule daily refresh at 7:00 AM.

### 10.2 Required DAX Measures

```dax
-- Win Rate
Win Rate =
    DIVIDE(
        COUNTROWS(FILTER('fact_opportunities', [is_won] = 1)),
        COUNTROWS(FILTER('fact_opportunities', [is_won] IN {0, 1}))
    )

-- Probability-Weighted Pipeline Value
-- More realistic than raw pipeline value
Weighted Pipeline =
    SUMX(
        'ML_PREDICTIONS',
        RELATED('fact_opportunities'[amount]) * [win_probability]
    )

-- Average Days to Close (Won deals only)
Avg Days to Close =
    AVERAGEX(
        FILTER('fact_opportunities', [is_won] = 1),
        [total_days_in_funnel]
    )

-- At-Risk Pipeline Value (probability < 40%)
At Risk Pipeline =
    SUMX(
        FILTER('ML_PREDICTIONS', [probability_band] = "LOW"),
        RELATED('fact_opportunities'[amount])
    )
```

### 10.3 Dashboard Pages

**Page 1 — Pipeline Command Centre**
- KPI cards: Total Pipeline Value, Probability-Weighted Pipeline, High Confidence Wins (>70%), At-Risk Deals (<40%)
- Scatter plot: X = Deal Value, Y = Win Probability, Size = Days in Funnel, Colour = Division
  - This creates 4 quadrants: Close Now / Rescue / Quick Wins / Consider Dropping
- Slicer: Division, Region, Agent, Date range

**Page 2 — Deal Funnel Analysis**
- Funnel chart: count + value at each CRM stage
- Bar chart: Win rate by Division (with year-over-year comparison)
- Map visual: Win rate by country/region
- Line chart: Monthly win rate trend (Jan 2015 → Dec 2024)

**Page 3 — Individual Deal Intelligence**
- Deal slicer (dropdown)
- Win probability gauge (0–100%, Red < 35%, Amber 35–60%, Green > 60%)
- SHAP factors table: top_positive_factors / top_negative_factors from ML_PREDICTIONS
- Line chart: how win probability changed as deal moved through stages
- Text card: `top_positive_factors` and `top_negative_factors` from ML_PREDICTIONS

**Page 4 — Agent Performance**
- Bar chart: Win rate per agent (sorted descending)
- Scatter: Agent workload (open deals) vs win rate
- Table: Agent, Division, Trailing 12m Win Rate, Open Deals, Avg Days to Close

**Page 5 — Client Intelligence**
- Bar chart: Top 20 clients by lifetime value
- Line chart: Win rate trend per client over time
- KPI: Clients with no activity in 90+ days (at-risk relationships)

**Page 6 — Revenue Forecast**
- Waterfall: Expected revenue by probability band (HIGH / MEDIUM / LOW)
- Comparison: Raw pipeline value vs probability-weighted value vs actual closed
- Table: Division, Open Deals, Raw Value, Weighted Value, Predicted Closures

---

## 11. Execution Order

When Claude Code is building this project, follow this exact sequence:

```
1.  dbt seed                          # load region_config.csv
2.  dbt run --select staging          # Bronze → Silver views
3.  dbt test --select staging         # validate all staging models
4.  dbt run --select intermediate     # cross-table aggregations
5.  dbt run --select mart             # Gold Star Schema tables
6.  dbt test --select mart            # validate Gold layer
7.  dbt run --select ml               # ML feature table
8.  dbt test --select ml              # validate no leakage, ranges
9.  python ml/01_eda.py               # EDA — run once, review outputs
10. python ml/02_train.py             # Train XGBoost, log to MLflow
11. python ml/03_evaluate.py          # Threshold optimisation
12. python ml/04_explain.py           # SHAP global + per-deal factors
13. python ml/05_score.py             # Score all open deals
14. python ml/06_write_predictions.py # Write ML_PREDICTIONS to Snowflake
15. Power BI — connect + build        # Import tables, build dashboards
```

---

## 12. Guardrails for Claude Code

1. **Never modify Bronze tables.** All transformation starts in `staging/`.
2. **Never use random train/test split.** Always split by `fiscal_year`.
3. **Never include post-close features** in `ml_deal_features.sql` — only features known at Negotiation entry.
4. **SMOTE applies to training data only** — never to validation or test sets.
5. **All credentials via environment variables** — never hard-coded.
6. **dbt model names must match exactly** the folder conventions: `stg_`, `int_`, `dim_`, `fact_`, `ml_`.
7. **Snowflake column names are UPPERCASE** — always quote or UPPER() when referencing in Python.
8. **MLflow must log every run** — no training without `mlflow.start_run()`.
9. **Decision threshold is 0.38**, not 0.5 — see Section 9.3 for business reasoning.
10. **`is_won` can be NULL** (open deals) — never fill NULLs with 0 in the target column.