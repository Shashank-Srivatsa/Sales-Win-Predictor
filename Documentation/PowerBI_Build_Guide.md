# Sales Win Predictor — Power BI Build Guide

> **Who this is for:** A salesperson or sales manager who wants to understand their live pipeline, act on ML predictions, and drill into individual deals.
>
> **Time to build:** ~45 minutes following this guide step by step.
>
> **Primary table:** `GOLD.FACT_OPPORTUNITIES_SCORED` — one row per deal, with ML predictions already joined. This is the only table you need for most visuals.

---

## Step 1 — Connect to Snowflake

1. Open **Power BI Desktop** → **Get Data** → search for **Snowflake**
2. Enter:
   - **Server:** `QACMQHK-SN72200.snowflakecomputing.com`
   - **Warehouse:** `COMPUTE_WH`
   - **Database:** `SALES_WIN_DB`
   - **Data connectivity mode:** `Import`
3. Sign in with your Snowflake username + password
4. In the Navigator, select these tables and click **Load**:

| Schema | Table | Used for |
|--------|-------|----------|
| GOLD | FACT_OPPORTUNITIES_SCORED | Every page (primary table) |
| GOLD | DIM_ACCOUNT | Client name, tier, industry |
| GOLD | DIM_USER | Agent name, division |
| GOLD | DIM_DATE | Date intelligence — **mark as Date Table** |
| GOLD | FACT_STAGE_HISTORY | Funnel analysis (Page 2) |
| ML | LLM_PREDICTIONS | LLM win probability + reasoning (Pages 7) |
| ML | MODEL_COMPARISON | XGBoost vs LLM side-by-side (Page 8) |

> **Important:** After loading, go to **Modeling** → select `dim_date` → click **Mark as date table** → choose `date_day`. This enables all time-intelligence DAX.

---

## Step 2 — Set Relationships

Go to **Model view** (left sidebar icon). Create these relationships:

| From (Many side) | To (One side) | Join column |
|---|---|---|
| `fact_opportunities_scored` | `dim_account` | `account_sk` |
| `fact_opportunities_scored` | `dim_user` | `user_sk` |
| `fact_opportunities_scored` | `dim_date` | `created_date_sk` → `date_sk` |
| `fact_stage_history` | `fact_opportunities_scored` | `opportunity_sk` |
| `LLM_PREDICTIONS` | `fact_opportunities_scored` | `opportunity_id` |
| `MODEL_COMPARISON` | `fact_opportunities_scored` | `opportunity_id` |

All relationships: **Single direction** (arrow pointing toward the dimension). Cardinality: **Many-to-one**.

> **Note for LLM tables:** `LLM_PREDICTIONS` and `MODEL_COMPARISON` only contain **open deals** (48 rows each). The join to `fact_opportunities_scored` on `opportunity_id` is the bridge to get deal value, account name, and agent name for display.

---

## Step 3 — Add All DAX Measures

1. In the **Fields** pane, right-click `fact_opportunities_scored` → **New measure**
2. Copy each measure from `Documentation/PowerBI_DAX_Measures.dax` into the formula bar
3. Organise measures into a **Display Folder** called `_Measures` (right-click measure → Properties → Display folder)

---

## Step 4 — Report Theme

Go to **View** → **Themes** → **Customize current theme**:

```
Background:    #1A1A2E   (dark navy)
Text:          #FFFFFF
Accent 1:      #2ECC71   (green — Won / HIGH)
Accent 2:      #E74C3C   (red — Lost / LOW)
Accent 3:      #F39C12   (amber — MEDIUM / warning)
Accent 4:      #3498DB   (blue — neutral info)
Font:          Segoe UI
```

---

## Page 1 — Pipeline Command Centre

**Purpose:** The first page a salesperson sees every morning. At a glance: total pipeline, weighted forecast, and which deals need rescue.

**Background:** Full-width dark header bar (rectangle shape, fill #2C3E50, no border).  
Add report title text: **"Sales Pipeline Intelligence"** (white, 20pt, Segoe UI Semibold).

### KPI Cards (top row — 4 cards side by side)

| Card | Measure | Format | Colour |
|------|---------|--------|--------|
| Total Pipeline | `Total Pipeline Value` | $#,##0 | White |
| Weighted Forecast | `Weighted Pipeline` | $#,##0 | #3498DB |
| High Confidence | `High Confidence Wins` | 0 "deals" | #2ECC71 |
| At Risk | `At Risk Pipeline` | $#,##0 | #E74C3C |

Format each card: **Turn off** title, **turn off** border, background transparent.

### Scatter Plot (centre — largest visual)

> This is the most powerful visual. It puts every open deal in a 2×2 quadrant.

- **Visual type:** Scatter chart
- **Filter:** `is_open = 1`
- **X-axis:** `amount` (field from table, not a measure) — label: "Deal Value (USD)"
- **Y-axis:** `win_probability` — label: "Win Probability"
- **Size:** `total_days_in_funnel` — label: "Days in Funnel"
- **Legend / colour:** `probability_band`
  - HIGH → #2ECC71 (green)
  - MEDIUM → #F39C12 (amber)
  - LOW → #E74C3C (red)
- **Details (tooltip):** `opportunity_id`, `stage`, `top_positive_factors`, `top_negative_factors`

**Add 4 quadrant labels** using Text Box shapes (no fill, white text, 9pt):
- Top-left: `"Quick Wins"` (low value, high probability)
- Top-right: `"Close Now"` (high value, high probability)
- Bottom-left: `"Consider Dropping"` (low value, low probability)
- Bottom-right: `"Rescue These"` (high value, low probability)

**Add reference lines:**
- Horizontal line at Y = 0.60 (dashed, grey, label: "60% threshold")
- Vertical line at X = median deal value (optional)

### Slicers (right sidebar)

Stack these slicers vertically:
1. `dim_user[full_name]` — label: "Agent"
2. `dim_account[division]` — label: "Division" *(use `fact_opportunities_scored[division]`)*
3. `fact_opportunities_scored[region]` — label: "Region"
4. `dim_date[fiscal_year]` — label: "Fiscal Year" (single select dropdown)

**Slicer style:** Dropdown, no border, dark background (#
), white text.

---

## Page 2 — Deal Funnel Analysis

**Purpose:** Understand where deals are dropping out and how win rate trends over time.

### Funnel Chart (top-left)

- **Visual type:** Funnel chart
- **Category:** Stage name (manual order: Lead → Qualified Lead → Opportunity → Negotiation → Closed Won)
- **Values:** Use these measures in a stacked bar instead if funnel chart doesn't support multiple measures:
  - `Deals Reached Lead`, `Deals Reached Qualified`, `Deals Reached Opportunity`, `Deals Reached Negotiation`, `Deals Closed Won`

> **Alternative:** Use a **Bar chart** with `fact_stage_history[to_stage]` on the axis and `COUNTROWS` as value, filtered to exclude Closed Lost. Sort by stage order.

### Bar Chart — Win Rate by Division (top-right)

- **Visual type:** Clustered bar chart
- **Y-axis (categories):** `fact_opportunities_scored[division]`
- **X-axis (values):** `Win Rate` and `Win Rate PY` (two bars per division)
- **Data labels:** On, format as percentage
- **Tooltip:** `Win Rate YoY Change`
- **Sort:** Descending by `Win Rate`

**Expected result (from SHAP analysis):** PulseMedia highest, BrandVault lowest — this should match the bar order.

### Line Chart — Monthly Win Rate Trend (bottom, full width)

- **Visual type:** Line chart
- **X-axis:** `dim_date[date_day]` (set to Month granularity)
- **Y-axis:** `Win Rate`
- **Legend:** `fact_opportunities_scored[division]` (one line per division)
- **Date range:** Use the fiscal year slicer from Page 1 (sync slicers across pages)
- **Format:** Y-axis 0–100%, data labels off (too crowded), markers on

### Map Visual (bottom-right, optional)

- **Visual type:** Map (or Shape Map with custom regions)
- **Location:** `dim_account[country]`
- **Size/colour:** `Win Rate`
- **Tooltip:** `Win Rate`, `Deals Closed Won`, `Open Deal Count`

---

## Page 3 — Individual Deal Intelligence

**Purpose:** A salesperson selects their deal from a dropdown and sees a full AI-powered briefing. This replaces manually digging through CRM notes.

**Layout:** Left column (1/3 width) = deal selector + summary stats. Right column (2/3 width) = probability gauge + AI explanation.

### Deal Selector Slicer (top-left)

- **Visual type:** Slicer (dropdown)
- **Field:** `fact_opportunities_scored[opportunity_id]`
- **Filter:** `is_open = 1`
- **Single select:** On
- **Label:** "Select Deal"

### Summary Cards (below slicer, left column)

Four small cards in a 2×2 grid:

| Card | Measure |
|------|---------|
| Deal Value | `Selected Deal Amount` → format $#,##0 |
| Current Stage | `Selected Deal Stage` |
| Days in Funnel | `Selected Deal Days in Funnel` |
| Win Probability | `Selected Deal Win Probability` → format 0.0% |

### Win Probability Gauge (top-right, large)

- **Visual type:** Gauge chart
- **Value:** `Selected Deal Win Probability`
- **Minimum:** 0, **Maximum:** 1, **Target:** 0.60
- **Colour:** Conditional formatting using Rules:
  - Value < 0.35 → fill #E74C3C (red)
  - Value 0.35 to 0.60 → fill #F39C12 (amber)
  - Value > 0.60 → fill #2ECC71 (green)
- **Data label:** Percentage format, large font (20pt)
- **Title:** "AI Win Probability"

### SHAP Factors (below gauge)

Two **Text card** visuals side by side:

**Left card — "Why this deal will WIN"**
- **Field:** `Selected Deal Top Positive Factors`
- **Background:** #1E5631 (dark green)
- **Text colour:** White
- **Title:** "Top Win Drivers" (white, bold)
- **Font:** 12pt

**Right card — "Risk factors"**
- **Field:** `Selected Deal Top Risk Factors`
- **Background:** #641E16 (dark red)
- **Text colour:** White
- **Title:** "Risk Signals" (white, bold)
- **Font:** 12pt

> These two cards update automatically when a different deal is selected in the slicer. No interaction needed — the SHAP factors from the ML pipeline flow directly into these cards.

### Deal Detail Table (bottom, full width)

A table showing all key deal attributes for context:

| Column | Field/Measure |
|--------|--------------|
| Agent | `dim_user[full_name]` |
| Account | `dim_account[account_name]` |
| Division | `fact_opportunities_scored[division]` |
| Lead Source | `fact_opportunities_scored[lead_source]` |
| Days in Negotiation | `fact_opportunities_scored[days_in_negotiation_stage]` |
| Last Activity | `fact_opportunities_scored[days_since_last_activity]` (label: "Days silent") |
| Probability Band | `fact_opportunities_scored[probability_band]` |
| Scored Date | `fact_opportunities_scored[prediction_date]` |

**Conditional formatting on Probability Band column:**
- HIGH → green background
- MEDIUM → amber background
- LOW → red background

---

## Page 4 — Agent Performance

**Purpose:** Sales manager view. Who is performing, who is overloaded, who needs coaching.

### Bar Chart — Win Rate per Agent (top, full width)

- **Visual type:** Bar chart (horizontal)
- **Y-axis:** `dim_user[full_name]`
- **X-axis:** `Agent Win Rate`
- **Sort:** Descending by win rate
- **Data labels:** On, percentage format
- **Conditional formatting on bars:** Same green/amber/red thresholds (0.60 / 0.35)
- **Filter:** Only agents with at least 5 closed deals (use filter pane: `Deals Closed Won >= 5`)

### Scatter — Workload vs Win Rate (middle-left)

- **Visual type:** Scatter chart
- **X-axis:** `Agent Open Deals` (measure)
- **Y-axis:** `Agent Win Rate`
- **Details:** `dim_user[full_name]` (one dot per agent)
- **Size:** `Actual Closed Revenue`
- **Reference line:** Vertical line at X=30 (label: "Overload zone")
- **Quadrant interpretation:**
  - Top-left: High win rate, low load → **Star performers** (give them more)
  - Top-right: High win rate, high load → **At risk of burnout** (reassign some)
  - Bottom-left: Low win rate, low load → **Needs coaching**
  - Bottom-right: Low win rate, high load → **Urgent intervention**

### Agent Summary Table (middle-right)

| Column | Source |
|--------|--------|
| Agent | `dim_user[full_name]` |
| Division | `dim_user[division]` |
| Seniority | `dim_user[seniority_level]` |
| Trailing 12m Win Rate | `dim_user[trailing_12m_win_rate]` |
| Open Deals | `Agent Open Deals` |
| Avg Days to Close | `Agent Avg Days to Close` |

**Sort:** Descending by trailing 12m win rate. Add data bars on the win rate column.

---

## Page 5 — Client Intelligence

**Purpose:** Identify the most valuable clients, at-risk relationships, and client-level win patterns.

### KPI Cards (top row)

| Card | Measure |
|------|---------|
| At-Risk Clients | `At Risk Clients` (90+ days silent) → red |
| Total Lifetime Value | `Client Lifetime Value` across all clients |
| Avg Client Win Rate | `Client Win Rate` |

### Bar Chart — Top 20 Clients by Lifetime Value (left)

- **Visual type:** Bar chart (horizontal)
- **Y-axis:** `dim_account[account_name]`
- **X-axis:** `Client Lifetime Value`
- **Top N filter:** Top 20 by `Client Lifetime Value`
- **Colour:** By `dim_account[account_tier]`
  - Tier 1 → #2ECC71 (top clients, green)
  - Tier 2 → #F39C12
  - Tier 3 → #95A5A6

### Line Chart — Win Rate Trend per Client (right)

- **Visual type:** Line chart
- **X-axis:** `dim_date[date_day]` (year granularity)
- **Y-axis:** `Client Win Rate`
- **Legend:** `dim_account[account_name]`
- **Filter:** Top 5 clients by lifetime value (so lines are readable)
- **Slicer:** Account selector so the user can swap in specific clients

### Client Risk Table (bottom, full width)

Clients with at least one open deal and no recent activity:

| Column | Field |
|--------|-------|
| Account | `dim_account[account_name]` |
| Industry | `dim_account[industry]` |
| Tier | `dim_account[account_tier]` |
| Open Deals | `Open Deal Count` |
| Days Since Last Activity | `fact_opportunities_scored[days_since_last_activity]` (max per account) |
| At-Risk Flag | Conditional format: days > 90 → red row |

**Filter:** `is_open = 1` and `days_since_last_activity > 60`.

---

## Page 6 — Revenue Forecast

**Purpose:** The CFO / sales director view. How much revenue is realistically coming in?

### Waterfall Chart — Pipeline by Band (left)

- **Visual type:** Waterfall chart
- **Category:** Manual sequence: "HIGH Confidence", "MEDIUM Confidence", "LOW / At Risk", "Probability-Weighted Total"
- **Values:**
  - HIGH Confidence → `Pipeline HIGH`
  - MEDIUM Confidence → `Pipeline MEDIUM`
  - LOW / At Risk → `Pipeline LOW`
  - Probability-Weighted Total → `Weighted Pipeline`
- **Colours:** GREEN for HIGH, AMBER for MEDIUM, RED for LOW

> **Alternative:** Use a stacked bar chart with three series (HIGH / MEDIUM / LOW) grouped by Division. This is easier to build and just as informative.

### Bar Chart — Raw vs Weighted vs Closed (right)

- **Visual type:** Clustered bar chart
- **X-axis:** `fact_opportunities_scored[division]`
- **Values (3 bars per division):**
  1. `Total Pipeline Value` (raw — what salespeople hope for)
  2. `Weighted Pipeline` (what the model thinks is realistic)
  3. `Actual Closed Revenue` (what has been booked)
- **Legend labels:** "Raw Pipeline", "ML Weighted", "Closed Revenue"
- **Learning note:** The gap between bar 1 and bar 2 is the "optimism discount" — how much the team is over-estimating their pipeline.

### Forecast Summary Table (bottom, full width)

| Column | Measure |
|--------|---------|
| Division | `fact_opportunities_scored[division]` |
| Open Deals | `Open Deal Count` |
| Raw Pipeline | `Total Pipeline Value` |
| Weighted Pipeline | `Weighted Pipeline` |
| HIGH Count | `High Confidence Wins` |
| LOW Value at Risk | `At Risk Pipeline` |
| Coverage Ratio | `Pipeline Coverage` |

**Conditional formatting:**
- Coverage Ratio < 2.0 → red (pipeline is thin)
- Coverage Ratio 2.0–4.0 → amber
- Coverage Ratio > 4.0 → green

---

## Page 7 — LLM Deal Intelligence

**Purpose:** For each open deal, show the LLM's natural language reasoning alongside its win probability. This is the "ask the AI why" page — a salesperson selects a deal and reads a plain-English explanation of what the model thinks.

**New tables used:** `LLM_PREDICTIONS`, `MODEL_COMPARISON`

**Background:** Same dark header bar as other pages. Title: **"LLM Deal Intelligence"** (white, 20pt).

### Deal Selector Slicer (top-left)

- **Visual type:** Slicer (dropdown)
- **Field:** `LLM_PREDICTIONS[opportunity_id]`
- **Single select:** On
- **Label:** "Select Deal"

### KPI Cards (top row — 3 cards)

| Card | Field/Measure | Format | Colour |
|------|--------------|--------|--------|
| LLM Win Probability | `LLM Selected Deal Probability` | 0.0% | Conditional (see below) |
| LLM Band | `LLM Selected Deal Band` | Text | Conditional (see below) |
| XGBoost Probability | `Selected Deal Win Probability` (from Page 3 measures) | 0.0% | #3498DB |

**Conditional formatting on LLM Win Probability card background:**
- Value < 0.40 → #E74C3C (red)
- Value 0.40–0.70 → #F39C12 (amber)
- Value > 0.70 → #2ECC71 (green)

**Conditional formatting on LLM Band card background:**
- Text = "LOW" → #E74C3C
- Text = "MEDIUM" → #F39C12
- Text = "HIGH" → #2ECC71

### LLM Reasoning Text Card (centre — largest visual)

> This is the most important visual on this page. It shows the LLM's written explanation in plain English.

- **Visual type:** Card (text)
- **Field:** `LLM Selected Deal Reasoning`
- **Title:** "LLM Reasoning" (white, bold)
- **Background:** #1A2744 (dark blue-navy, slightly lighter than page background)
- **Text colour:** White
- **Font size:** 13pt
- **Word wrap:** On
- **Border:** 1px solid #3498DB (blue accent)
- **Height:** Tall — allow ~4 lines of text
- **No value:** Show "Select a deal above"

> **Note:** This text is generated by `llama3.2:3b` via Ollama for each deal. It references specific deal signals (velocity, discount, engagement) rather than generic statements.

### Comparison Bar Chart (bottom — full width)

Shows XGBoost vs LLM probability for the selected deal side by side.

- **Visual type:** Clustered bar chart
- **Y-axis (categories):** Two static labels — create a disconnected table with values `{"XGBoost", "LLM"}` (see tip below)
- **X-axis (values):** `Selected Deal Win Probability` for XGBoost bar, `LLM Selected Deal Probability` for LLM bar
- **Colour:** XGBoost bar → #3498DB (blue), LLM bar → #9B59B6 (purple)
- **Data labels:** On, percentage format
- **X-axis range:** 0 to 1
- **Reference line:** Vertical at 0.60 (dashed grey, label: "Decision threshold")
- **Title:** "Model Comparison — Selected Deal"

> **Tip for the two-bar chart:** The easiest approach is a simple **two-card layout** instead of a bar chart — one card per model, placed side by side. Label them "XGBoost" and "LLM RAG" with their respective probability measures. Simpler to build and equally readable.

---

## Page 8 — Model Agreement Dashboard

**Purpose:** Surface the 4 deals where XGBoost and the LLM significantly disagree (delta > 0.25). These disagreements are not errors — they are the most analytically interesting deals, where quantitative patterns and qualitative reasoning diverge. Flag them for human review.

**New tables used:** `MODEL_COMPARISON`

**Background:** Same dark theme. Title: **"Model Agreement Dashboard"** (white, 20pt).

### KPI Cards (top row — 3 cards)

| Card | Measure | Format | Colour |
|------|---------|--------|--------|
| Model Agreement Rate | `Model Agreement Rate` | 0.0% | #2ECC71 (green — high agreement is good) |
| High Disagreement Deals | `High Disagreement Deals` | 0 "deals" | #E74C3C (red — these need attention) |
| Total Deals Compared | `COUNTROWS('MODEL_COMPARISON')` | 0 "deals" | White |

### Disagreement Deals Table (centre-left — ~60% width)

Shows only the 4 deals where the models diverge significantly.

- **Visual type:** Table
- **Filter:** `MODEL_COMPARISON[DISAGREEMENT_FLAG] = TRUE`
- **Columns:**

| Column | Field | Format |
|--------|-------|--------|
| Deal ID | `MODEL_COMPARISON[OPPORTUNITY_ID]` | Text |
| XGBoost Prob | `MODEL_COMPARISON[XGB_WIN_PROBABILITY]` | 0.0% |
| LLM Prob | `MODEL_COMPARISON[LLM_WIN_PROBABILITY]` | 0.0% |
| Delta | `MODEL_COMPARISON[PROBABILITY_DELTA]` | 0.0% |
| Higher Confidence | `MODEL_COMPARISON[HIGHER_CONFIDENCE_MODEL]` | Text |
| LLM Reasoning | `MODEL_COMPARISON[LLM_REASONING]` | Text (wrap on) |

**Conditional formatting:**
- `XGB_WIN_PROBABILITY` column: colour scale — red (0) → green (1)
- `LLM_WIN_PROBABILITY` column: colour scale — red (0) → green (1)
- `PROBABILITY_DELTA` column: background → white below 0.25, #E74C3C above 0.25
- `HIGHER_CONFIDENCE_MODEL` column: "XGB" → #3498DB background, "LLM" → #9B59B6 background

**Sort:** Descending by `PROBABILITY_DELTA` (largest disagreements first).

### Scatter Plot — All 48 Deals (right — ~40% width)

Every dot is one open deal. Dots close to the diagonal = models agree. Dots far from the diagonal = models disagree.

- **Visual type:** Scatter chart
- **X-axis:** `MODEL_COMPARISON[XGB_WIN_PROBABILITY]` — label: "XGBoost Probability"
- **Y-axis:** `MODEL_COMPARISON[LLM_WIN_PROBABILITY]` — label: "LLM Probability"
- **Details:** `MODEL_COMPARISON[OPPORTUNITY_ID]` (one dot per deal)
- **Colour:** `MODEL_COMPARISON[DISAGREEMENT_FLAG]`
  - FALSE (agreement) → #3498DB (blue)
  - TRUE (disagreement) → #E74C3C (red)
- **Size:** Fixed (no size field — keep it simple)
- **X-axis range:** 0 to 1
- **Y-axis range:** 0 to 1
- **Title:** "XGBoost vs LLM — All Open Deals"

**Add diagonal reference line (perfect agreement line):**
Power BI scatter charts don't natively draw Y=X lines. Add it using a **constant line** workaround:
1. Add a trend line (Analytics pane → Trend line) — this approximates the diagonal
2. Or add a text annotation "← Agreement line" near the diagonal manually

**How to read this chart:**
- Dots in the **top-left** (LLM high, XGBoost low): LLM is more optimistic — deal has positive qualitative signals the numbers miss
- Dots in the **bottom-right** (XGBoost high, LLM low): XGBoost is more optimistic — deal has good numerical features but LLM sees risk in the narrative
- Red dots = the 4 flagged disagreement deals — investigate these manually

### Full Comparison Table (bottom — full width, all 48 deals)

- **Visual type:** Table (no filter — all deals)
- **Columns:** `OPPORTUNITY_ID`, `XGB_WIN_PROBABILITY`, `XGB_PROBABILITY_BAND`, `LLM_WIN_PROBABILITY`, `LLM_PROBABILITY_BAND`, `PROBABILITY_DELTA`, `MODELS_AGREE`
- **Conditional formatting on MODELS_AGREE:** TRUE → green background, FALSE → red background
- **Sort:** Descending by `PROBABILITY_DELTA`
- **Title:** "All Deals — Model Comparison"

---

## Step 5 — Cross-Page Slicer Sync

In Power BI: **View** → **Sync slicers**

Sync these slicers across all pages so selections carry through:
- Division slicer → sync to Pages 1, 2, 4
- Fiscal Year slicer → sync to Pages 1, 2, 6
- Agent slicer → sync to Pages 1, 3, 4

---

## Step 6 — Publish and Schedule Refresh

1. **File** → **Publish** → choose your Power BI workspace
2. In **app.powerbi.com**: find the dataset → **Schedule Refresh**
   - Frequency: Daily
   - Time: 07:00 AM (after the nightly ML scoring + dbt run completes)
   - Snowflake credentials: enter once in dataset settings

---

## Daily Data Flow Reminder

Run these three commands before Power BI refreshes each morning:

```
python ml/06_write_predictions.py
cd sales_win_predictor && dbt run --select fact_opportunities_scored
```

Power BI then picks up the fresh predictions automatically on scheduled refresh.

---

## What the Salesperson Sees Each Morning

1. **Page 1:** Scatter plot — which open deals are in the "Rescue" quadrant?
2. **Page 3:** Select any deal → gauge + SHAP factors → immediate briefing on what's driving the ML score
3. **Page 4:** Is my workload sustainable? Am I overloaded vs my win rate?
4. **Page 6:** Is my division's weighted pipeline healthy for the quarter?

The `top_positive_factors` and `top_negative_factors` text cards on Page 3 are the most actionable output — they tell the salesperson *why* the model thinks a deal is at risk, in plain feature names, without needing to understand the ML model at all.
