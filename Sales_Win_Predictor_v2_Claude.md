

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 1
## Confidential — For Personal Use Only
u
## PROJECT SPECIFICATION DOCUMENT
## Sales Win Predictor
AI-Powered Deal Intelligence System
Built by a Data Engineer | Microsoft-First Stack
SQL Server · SSIS · Snowflake · dbt · Python · Power BI · Azure DevOps
XGBoostSHAPMLflowSMOTEFeature Eng.GenAIBatch Scoring
Who builds itYou — a Data Engineer working solo on this project
Business contextGlobal multi-vertical company: Talent, Marketing, Licensing, Content
Data sourceEnterprise CRM (similar to Salesforce) — 5–10 years of historical deal data
What the AI doesPredicts Win/Loss probability for every active CRM deal
Business valuePrioritise pipeline, rescue at-risk deals, probability-weighted revenue forecast
Your timeline4 weeks end-to-end, portfolio-ready on Day 28
## Version 2.0 · 2026 · Confidential — Solo Project

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 2
## Confidential — For Personal Use Only
Table of Contents
## 01
## Executive Summary
## 02
## Problem Statement — Business & Technical
## 03
## Industry & Business Modelling
## 04
## Data Modelling Overview
## 05
## Feature Engineering (40+ Features)
## 06
Data Engineering Pipeline — Step by Step
## 07
## Machine Learning Design
## 08
Implementation Plan — Phase by Phase
## 09
## Deployment Strategy
## 10
Power BI Dashboard — Overview
## 11
## System Architecture
## 12
Advanced Features — SHAP, GenAI, Recommendations
## 13
## Learning Roadmap
## 14
4-Week Day-by-Day Execution Plan

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 3
## Confidential — For Personal Use Only
## 01
## Executive Summary
You are a Data Engineer at a BI-as-a-Service company. Your primary client is a large global entertainment and talent
conglomerate  —  referred  to  in  this  document  as  GlobalTalent  Group  —  which  operates  four  business  divisions:
TalentEdge  (models,  photographers,  creative  talent),  CreativeMotion  (content  writers,  directors,  designers),
PulseMedia  (marketing  agency),  and  BrandVault  (brand  licensing).  All  four  divisions  run  on  a  CRM-driven  sales
model — leads become deals, deals become revenue.
The  Sales  Win  Predictor  is  an  AI  system  you  will  build  end-to-end,  alone,  using  tools  you  already  know.  It  learns
from years of historical CRM deal data and predicts, for every active deal, the probability it will be Won or Lost. The
result is a Power BI dashboard that sales teams can act on every morning.
What the System Delivers
- Win Probability Score (0–100%): Every active deal gets a score, refreshed daily.
- Explainability (SHAP): Tells you WHY a deal is at risk — not just that it is.
- Recommendations: "Reduce discount from 31% to below 20% → +12pp win probability."
- GenAI Deal Summaries: Auto-written 3-sentence risk brief for each deal, shown in Power BI.
- Revenue Forecast: Probability-weighted pipeline value — realistic expected revenue per quarter.
## Impact Summary
MetricWithout SystemWith System (Target)
Win Rate~38%Target 47–52% (+9 percentage points)
Deal PrioritisationManual / gut feelML-ranked pipeline — highest-value deals first
Agent Review Time3–5 hrs/week per agentUnder 30 min with AI-generated deal summaries
Revenue Forecast Accuracy±25% error±8–12% (probability-weighted method)
At-Risk Deal DetectionFound too late to actEarly warning 5–7 days before deals go cold
n PERSONAL NOTE: This project is designed for you to build alone, step by step.
Every section maps to a real skill you need to close the gap from Data Engineer
to AI-enabled Data Engineer — which is exactly what companies hire for today.
Build it. Understand every line. It will change your interviews.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 4
## Confidential — For Personal Use Only
## 02
## Problem Statement — Business & Technical
## 2.1 The Business Problem
Imagine  the  analytics  head  at  GlobalTalent  Group  opens  their  Monday  pipeline  report.  There  are  83  open  deals
across  all  four  divisions.  A  $2.8M  sportswear  brand  campaign  is  in  Negotiation.  A  character-logo  licensing  deal  is
stalled for 34 days. A small $45K model booking is the only one about to close. Without an intelligent system, no one
can answer:
- Which of our 83 open deals is most likely to close this month?
- Is the sportswear deal at risk — should we escalate it?
- Which deals are we wasting agent time on that will never close?
- What is our realistic revenue forecast for this quarter?
Without  this  system,  decisions  are  made  on  intuition.  High-value  deals  get  insufficient  attention.  Low-value  deals
consume disproportionate agent time. Revenue leaks from the bottom of the funnel unnoticed.
## 2.2 The Technical Problem
## Data Fragmentation
- CRM data (deals, leads, contracts) arrives through your existing pipeline — SQL Server → SSIS → Snowflake.
- Employee hours, agent data, and line items live in separate tables with different schemas per division.
- 10 years of data with schema drift, missing values, and regional naming inconsistencies needs careful cleaning.
## Feature Engineering Complexity
-  A  deal's  win/loss  outcome  depends  on  40+  variables  —  deal  size,  agent  history,  client  behaviour,  time  pressure,
discount levels.
- Most powerful features are NOT stored directly — they must be computed from historical patterns using dbt SQL.
- Time-based features must be computed carefully to avoid data leakage (a critical ML concept this project will teach
you).
## Class Imbalance
- In most CRMs, Won deals are only 35–45% of closed deals. A model that always says "Lost" gets 60% accuracy —
and is completely useless.
- You must use SMOTE oversampling and threshold optimisation to handle this correctly.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 5
## Confidential — For Personal Use Only
Real Cost of Getting This Wrong:
A $1.4M licensing deal stalls in Negotiation for 29 days (average is 12 days).
No agent notices — they are managing 40 other deals.
The deal goes cold. The client signs with a competitor.
Lost profit at 35% margin = $490,000 gone.
A Sales Win Predictor would have flagged this 15 days earlier:
"Deal stalled 2.4x longer than average for similar licensing deals.
Recommended action: Senior agent escalation within 48 hours."

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 6
## Confidential — For Personal Use Only
## 03
## Industry & Business Modelling
## 3.1 The Four Business Divisions
GlobalTalent  Group  operates  four  divisions,  each  generating  revenue  differently.  Understanding  this  is  critical
because your ML model must handle all four in a single unified system.
DivisionWhat They DoRevenue ModelExample Deal
TalentEdgePhotographers, stylists, makeup
artists, creative directors, models.
Agents manage talent rosters.
Commission on day-rate
bookings. Agent books
talent for client
shoot/campaign.
Sportswear brand books photographer 3 days
@ $4,500/day + creative director 5 days @
## $3,200/day.
CreativeMotionScriptwriters, directors, content
writers, designers. Produces media
and campaign content.
Project-based fixed fee +
talent placement
commission.
Apparel brand commissions a product launch
video: creative direction $15K + production
## $80K.
PulseMediaFull marketing agency. Campaign
strategy, digital, social, branding.
Staff log hours to deals.
Billable hours (rate by
seniority) OR fixed project
fee.
## Director 60hrs × $220 + 2 Managers 120hrs ×
## $130 + 3 Associates 240hrs × $80 = $56,400.
BrandVaultMiddleman between trademark
owners (cartoon characters, sports
logos) and brands wanting
licences.
## Minimum Guarantee
(upfront) + Royalty % on
net sales above MG
threshold.
Footwear brand wants character logo. MG =
$420K + 7.5% royalty on sales above $560K.
3.2 The CRM — Your Primary Data Source
All  four  divisions  use  a  single  enterprise  CRM  (similar  in  structure  to  Salesforce)  to  record  every  lead,  deal,  client
interaction, and contract. This CRM is the data source your existing pipeline already ingests. It contains 5–10 years of
closed deal history — which is what you will train the ML model on.
- Sales agents log every lead, call, meeting, proposal, line item, and pricing change into the CRM.
- You receive this data through your existing SSIS → SQL Server → Snowflake pipeline.
- You have access to the raw data and pipeline — not the final client-facing reports. That is exactly what you need.
3.3 Deal Funnel vs. Deal Pipeline
ConceptWhat It Means & How This System Uses It
DEAL FUNNEL (Conversion View)A vertical view showing what % of deals survive each stage. Answers: WHERE are we losing
deals? Example: 100 leads enter → 60 qualify → 35 reach Opportunity → 18 reach Negotiation →
11 close as Won. The 11% end-to-end conversion rate is the funnel metric.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 7
## Confidential — For Personal Use Only
DEAL PIPELINE (Forecast View)A horizontal view of all currently ACTIVE deals with expected values and close dates. Answers:
What revenue will close this quarter? Example: $14.2M in active deals — $3.1M in Negotiation,
$6.4M in Opportunity, $4.7M in Qualified stage.
Five-Stage Deal Funnel (CRM Stages)
StageWhat Happens HereTypical DurationML Signal
LeadBrand shows initial interest. Agent logs it in
## CRM.
1–7 daysLead source, brand tier
Qualified LeadBudget confirmed. Decision-maker engaged.
Real need exists.
3–14 daysTime to qualify, agent assigned
OpportunityScope building: line items drafted, rates
discussed, team assembled.
7–30 daysLine item count, deal value
NegotiationCommercial terms finalised. Contract
redlined. Final pricing agreed.
5–21 daysDiscount %, revision count, days stalled
Won / LostContract signed = Won. Client disengaged =
## Lost.
—TARGET VARIABLE: is_won (1/0)
## 3.4 How Line Items Work
Every deal is composed of Line Items — individual billable components. Line item structure is one of the strongest
predictors of win or loss. More items = more to negotiate = higher risk.
DivisionLine Item TypePricing LogicExample
TalentEdgeTalent Day RateDay rate × days bookedPhotographer × 3 days @ $4,500 = $13,500
TalentEdgeUsage RightsFlat fee by geography +
duration
US print rights 1 year = $8,000
PulseMediaBillable HoursHours × seniority rateManager × 80 hrs @ $130/hr = $10,400
PulseMediaProject FeeFixed negotiated amountFull campaign package = $85,000
BrandVaultMinimum GuaranteeUpfront fee based on brand
value
Character logo MG = $420,000
BrandVaultRoyalty %% of net sales above MG7.5% on sales above $560,000

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 8
## Confidential — For Personal Use Only
## 04
## Data Modelling Overview
The data model for this project uses a Star Schema — a standard pattern for analytical workloads that works natively
with  dbt,  Snowflake,  and  Power  BI.  You  do  not  need  to  memorise  every  column.  The  goal  is  to  understand  the
structure and purpose of each table so you know where your features come from.
Star Schema in Plain English:
One central FACT table (what happened — numbers and IDs).
Surrounded by DIMENSION tables (who, what, where, when — descriptive details).
Fact tables have FK columns pointing to dimension tables.
This structure makes GROUP BY and JOIN queries simple and fast in Snowflake.
## 4.1 Tables You Will Build
Table NameTypeWhat It StoresKey Columns
dim_dealDimensionOne row per deal. All deal attributes.deal_id, vertical, region, deal_type, client_id,
agent_id, is_won (TARGET)
dim_clientDimensionOne row per client brand (Nike, Adidas
etc).
client_id, client_name, industry, client_tier,
is_repeat_client
dim_agentDimensionOne row per sales agent.agent_id, seniority_level, specialisation, region,
hire_date
dim_dateDimensionOne row per calendar date (standard
date spine).
date_id, year, quarter, month,
is_fiscal_quarter_end
fact_deal_snapshotFact (CORE)One row per deal per stage transition.
Captures state of the deal at each point
in time.
deal_id, snapshot_date, current_stage,
deal_value, discount_pct, line_item_count,
days_in_funnel, is_won
fact_line_itemsFactEvery individual billable item on every
deal.
line_item_id, deal_id, type, unit_price, quantity,
discount, net_price
fact_stage_historyFactEvery stage transition a deal went
through.
deal_id, from_stage, to_stage, date_entered,
date_exited, days_in_stage
Why a Snapshot Table? (Important Concept)
The fact_deal_snapshot table is the most important design decision in this project. Instead of one flat row per deal, it
captures the deal's state at each stage transition. This lets you train the model on "what a deal looked like when it
entered Negotiation" — which is exactly when you still have time to take action to save it.
DesignOne flat row per dealSnapshot table (what we use)
Data capturedOnly final state — deal closedState at every stage transition

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 9
## Confidential — For Personal Use Only
Can you answer "how long was it stalled?"No — only final dates storedYes — days_in_stage per snapshot
Can you train on Negotiation-stage state?No — you only have end resultYes — filter WHERE current_stage =
## Negotiation
Best for ML?No — loses temporal contextYes — enables time-aware features
4.2 How the Tables Relate
RelationshipCardinalityWhat It Means
dim_client → dim_deal1 client : many dealsNike has had 40 deals over 10 years
dim_agent → dim_deal1 agent : many dealsEach deal is assigned to one lead agent
dim_deal → fact_deal_snapshot1 deal : many snapshotsOne snapshot per stage the deal passes through
dim_deal → fact_line_items1 deal : many line itemsA Nike campaign has 6 line items (talent, usage rights,
production)
dim_date → fact_deal_snapshot1 date : many snapshotsAllows filtering and time-series analysis by date

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 10
## Confidential — For Personal Use Only
## 05
## Feature Engineering (40+ Features)
Feature engineering is the most important skill in this entire project. A simple model with excellent features will
beat  a  complex  model  with  weak  features.  Each  feature  below  is  motivated  by  a  specific  business  hypothesis.
Understanding the "why" behind every feature is what separates you in interviews.
5.1 Deal-Level Features
Feature NameHow to Compute (dbt SQL)Business Hypothesis
deal_value_logLN(deal_value + 1)Log-transform reduces skew from large licensing deals. Larger
deals have lower win rates.
discount_pctDirect from snapshot tableModerate discounts (10–20%) help. Over 30% signals
desperation. Win rate drops to ~18%.
line_item_countCOUNT(*) from fact_line_itemsMore line items = more negotiation surface = higher chance of
disagreement and loss.
deal_complexity_scoreline_item_count × COUNT(DISTINCT
type)
Multi-type deals (talent + licensing + production) are harder to
close in one go.
total_days_in_funnelsnapshot_date − created_dateDeals stale beyond 90 days have historically low win rates.
Captures staleness.
days_in_negotiationDays since Negotiation stage entryNegotiations over 21 days frequently result in loss. Single
strongest stage-level signal.
contract_revision_countCOUNT revisions from stage historyMore than 3 contract revisions strongly predicts loss — client is
not committed.
deal_velocity_scoreexpected_median_days /
actual_days_in_funnel
Score > 1: moving faster than average (positive). Score < 0.5:
dangerously slow.
competitor_mentionedBoolean flag from CRM notesCompetitor mention lowers win rate by ~18 percentage points
historically.
is_renewaldeal_type = RenewalRenewals win at ~2x the rate of new business deals.
discount_risk_scoreTiered 0–1 score from discount_pct
buckets
Captures the non-linear impact: low discount fine, high discount
= alarm.
5.2 Client-Level Features
Feature NameComputed FromBusiness Hypothesis
client_historical_win_ratewon_deals / closed_deals per client
(all history)
Sticky clients win more. Declining rate is an early
warning of relationship cooling.
client_is_new1 if no prior closed deal existsNew clients win at ~30% vs ~52% for established clients.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 11
## Confidential — For Personal Use Only
client_tierDerived from lifetime deal value (Tier
## 1/2/3)
Tier 1 clients receive more agent attention and close
more reliably.
days_since_last_dealToday − date of last closed dealGaps above 180 days indicate a cooling relationship.
client_deal_countCOUNT of all historical dealsHigh-volume clients are well understood — predictions
are more reliable.
5.3 Agent-Level Features
Agent  features  are  among  the  strongest  predictors.  You  already  have  the  skills  for  this  —  your  existing  employee
capability model (hours vs. expected hours by tier and region) uses the same logic. Here you extend it to win rates.
Feature NameComputed FromBusiness Hypothesis
agent_trailing_12m_win_rateWon / closed deals, last 12 monthsSingle strongest agent predictor. 51% vs 28% win rate
agents are fundamentally different.
agent_win_rate_this_verticalWin rate for THIS deal's division onlyA PulseMedia agent pitching a BrandVault licensing deal
will underperform vs a specialist.
agent_current_workloadCOUNT open deals assigned right
now
Agents managing over 35 deals simultaneously show
lower win rates per individual deal.
agent_seniority_scoreJunior=1, Mid=2, Senior=3,
## Director=4
Senior agents close harder, higher-value deals through
relationship capital.
agent_client_familiarityCOUNT prior closed deals with this
specific client
Prior relationship with the client is a very strong positive
signal.
is_vertical_specialist1 if agent specialisation = deal's
division
Division mismatch predicts loss more reliably than most
other single features.
## 5.4 Time & Context Features
FeatureWhy It Matters
fiscal_quarter_end_flagCompanies rush to finalise deals before quarter-end. Last 2 weeks of fiscal quarter =
strong positive signal.
days_until_quarter_endUrgency ramps as this hits zero. Non-linear effect — very powerful when combined with
deal stage.
deal_created_monthSeasonal patterns differ between Q2 and Q4 in fashion and licensing businesses.
response_time_since_last_contactDays since last client interaction logged in CRM. Silence = disengagement.
year_deal_createdControls for macro-economic context (e.g. COVID-affected years in training data).
5.5 Two Important Derived Features (Advanced)

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 12
## Confidential — For Personal Use Only
## Deal Velocity Score
Formula: deal_velocity_score = expected_median_days / actual_days_in_funnel
Score > 1.0 → Deal moving FASTER than historical average → Positive signal
Score < 0.5 → Deal moving MUCH SLOWER than average → Strong negative signal
How to build in dbt: Compute expected_median_days from historical closed deals
grouped by division + deal_size_bucket, then LEFT JOIN this value back onto
each open deal row as a new column. This is a lookup-enrichment join —
the same pattern you already use in your existing dbt models.
## Client Engagement Score
Formula: (interactions in last 14 days) / (total interactions in deal lifetime) × recency_weight
Score > 0.6 → Client actively engaged recently → Strong positive signal
Score < 0.2 → Client engagement has dropped off → Deal going cold — act now
Why it matters: A client that stops responding is the clearest leading indicator
a deal will be lost. This feature captures that pattern before the deal officially stalls.
It is computed from the CRM interaction/activity log table.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 13
## Confidential — For Personal Use Only
## 06
Data Engineering Pipeline — Step by Step
The  pipeline  follows  the  Medallion  Architecture  (Bronze  →  Silver  →  Gold)  that  is  standard  at  enterprise  data
companies. 80% of this is work you already do — the ML layer is a natural extension of your Gold layer.
n
SOURCE — Enterprise CRM
SQL Server | All deal, agent, client, line item, and interaction data
t
nn
BRONZE — Raw Landing (Snowflake RAW Schema)
SSIS incremental extraction | Immutable raw tables | raw_deals, raw_agents, raw_line_items
t
n
SILVER — Cleaned & Standardised (Snowflake STAGING Schema)
dbt staging/ models | Deduplication, type casting, vertical name normalisation
t
n
GOLD — Star Schema Business Layer (Snowflake MART Schema)
dbt mart/ models | dim_deal, dim_client, dim_agent, fact_deal_snapshot, fact_line_items
t
n
ML LAYER — Feature Table (Snowflake MART Schema)
dbt ml/ model | ml_deal_features — one row per closed deal, all features pre-computed
t
n
PYTHON ML — Training & Scoring
XGBoost + SMOTE + SHAP | MLflow tracking | Daily batch scoring of open deals
t
n
POWER BI — Dashboards
Connects directly to Snowflake MART | Reads ML_PREDICTIONS table daily
## 6.1 Pipeline Layer Details
StageTool You UseWhat It Produces
SOURCE (SQL Server
## CRM)
Your existing SSIS pipeline already
connects here
Raw relational CRM tables: deals, contacts, line items,
stage history, interactions
BRONZE (Snowflake
## RAW)
SSIS → Snowflake COPY INTO Scheduled
daily at 2 AM
Immutable raw tables. Never update/delete. Every row has
an extracted_at timestamp.
SILVER (Snowflake
## STAGING)
dbt staging/ models Runs after SSIS at 6
## AM
Cleaned, deduplicated, standardised. One row per entity
per most recent version.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 14
## Confidential — For Personal Use Only
GOLD (Snowflake MART)dbt mart/ models Star schemaBusiness-ready Star Schema. fact_deal_snapshot is the
most important table.
ML LAYER (Snowflake
## MART)
dbt ml/ model ml_deal_features.sqlOne row per closed deal with all 40+ features
pre-computed. Python reads this directly.
6.2 Critical SSIS Rule
BRONZE LAYER RULE: Never UPDATE or DELETE rows in raw tables.
If a deal is updated in the CRM, SSIS lands a NEW row with a newer extracted_at timestamp.
The Silver dbt model handles deduplication — it keeps only the latest version per deal_id.
This makes your pipeline fully auditable and replayable — a key enterprise engineering standard.
You already follow this pattern at work. Apply it the same way here.
6.3 dbt Project Structure
FolderWhat Lives Here
models/staging/One .sql file per source table. Cleans, casts types, deduplicates. Example: stg_crm_deals.sql
models/intermediate/Multi-table logic before the mart. Example: int_agent_performance.sql computes rolling
12-month win rates per agent.
models/mart/Final Star Schema tables: dim_deal, dim_client, dim_agent, dim_date, fact_deal_snapshot,
fact_line_items.
models/ml/ml_deal_features.sql — joins all mart tables and computes derived features. This is the
Python model input.
tests/Data quality tests: unique keys, not_null constraints, referential integrity, value range checks.
macros/Reusable SQL logic. Example: fiscal_quarter_end() macro used across multiple models.
seeds/Static lookup tables loaded as CSVs. Example: region_expected_hours.csv for the capability
model logic you built.
6.4 Key dbt Model — stg_crm_deals.sql
This is a typical staging model. Read it carefully — every line has a purpose.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 15
## Confidential — For Personal Use Only
-- models/staging/stg_crm_deals.sql
-- Purpose: clean and standardise raw CRM deals from the Bronze layer
WITH source AS (
SELECT * FROM {{ source("raw_crm", "raw_crm_deals") }}
## ),
-- Step 1: Deduplicate — keep the most recently extracted version of each deal
deduped AS (
## SELECT *,
## ROW_NUMBER() OVER (
PARTITION BY crm_deal_id
ORDER BY extracted_at DESC
) AS rn
FROM source
## ),
-- Step 2: Clean and standardise columns
cleaned AS (
## SELECT
crm_deal_id::VARCHAR AS deal_source_crm_id,
TRIM(UPPER(deal_name)) AS deal_name,
-- Standardise vertical names from different CRM entry formats
## CASE
WHEN vertical ILIKE '%model%' THEN 'Talent'
WHEN vertical ILIKE '%creative%' THEN 'Content'
WHEN vertical ILIKE '%media%' THEN 'Marketing'
WHEN vertical ILIKE '%licens%' THEN 'Licensing'
ELSE 'Other'
END AS vertical_clean,
COALESCE(deal_value, 0)::FLOAT AS deal_value,
TRY_TO_DATE(created_date, 'YYYY-MM-DD') AS created_date,
-- Create the ML target label
CASE WHEN final_stage = 'Won' THEN 1 ELSE 0 END AS is_won
FROM deduped
WHERE rn = 1 -- keep only the latest version of each deal
## )
SELECT * FROM cleaned
6.5 Key dbt Model — ml_deal_features.sql
This is the final output table — the Python model's direct input. One row per closed deal. All features pre-computed.
The  most  important  design  rule:  no  data  leakage  —  only  include  features  that  would  be  known  at  the  time  of
prediction.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 16
## Confidential — For Personal Use Only
-- models/ml/ml_deal_features.sql
-- One row per CLOSED deal with all features. Python reads this directly.
WITH snap AS (
-- Use the snapshot at Negotiation stage — best balance of data richness and actionability
SELECT * FROM {{ ref("fact_deal_snapshot") }}
WHERE current_stage = 'Negotiation'
## ),
agent_perf AS (
SELECT * FROM {{ ref("int_agent_performance") }}
## ),
client_hist AS (
SELECT * FROM {{ ref("stg_crm_clients") }}
## )
## SELECT
snap.deal_id,
-- Deal features
snap.deal_value,
LN(snap.deal_value + 1) AS deal_value_log,
snap.discount_pct,
snap.line_item_count,
snap.total_days_in_funnel,
snap.days_in_current_stage AS days_in_negotiation,
snap.num_contract_revisions,
snap.agent_workload_at_time,
snap.competitor_flagged,
-- Agent features
ap.agent_trailing_12m_win_rate,
ap.agent_seniority_score,
ap.agent_client_familiarity,
-- Client features
ch.client_historical_win_rate,
ch.client_is_new,
ch.client_tier,
-- TARGET LABEL (only present for closed deals)
snap.is_won AS target
FROM snap
LEFT JOIN agent_perf ap ON snap.lead_agent_id = ap.agent_id
LEFT JOIN client_hist ch ON snap.client_id = ch.client_id
-- Only closed deals for training. Open deals scored separately.
WHERE snap.is_won IS NOT NULL

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 17
## Confidential — For Personal Use Only
DATA LEAKAGE WARNING — Features to NEVER include in ml_deal_features:
actual_close_date — only known after the deal closes
final_deal_value — the post-negotiation agreed price
contract_signed_by — only known after a won deal
Safe features (known at Negotiation entry):
discount_pct, line_item_count, days_in_funnel, agent_workload, client_tier
Leakage is the #1 reason ML models appear to work in training
but completely fail in production. You must verify this carefully.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 18
## Confidential — For Personal Use Only
## 07
## Machine Learning Design
## 7.1 Problem Framing
## Problem Type: Binary Classification
Input: ~40 engineered features per deal (deal, agent, client, time context)
Output: P(Win) in range [0.0 to 1.0] — probability score + binary label
Training Data: All CLOSED deals (Won or Lost) from historical CRM
Target Label: is_won (1 = Won, 0 = Lost)
Train/Test: Chronological split — train on deals before Dec 2022, test on 2023+
## 7.2 Model Selection
ModelWhy Consider ItDecision
Logistic RegressionSimple, fast, interpretable. Easy to explain to any
stakeholder.
Use as BASELINE. Establishes the minimum
acceptable performance.
Random ForestHandles non-linearity and missing values well.
Robust to noise.
Use as SECONDARY model. Good fallback if
XGBoost overfits.
XGBoostState-of-the-art on tabular CRM data. Fast. Handles
imbalance.
PRIMARY PRODUCTION MODEL. Best performance
on this type of data.
Neural NetworkPowerful, but needs 100K+ rows to beat tree
models on tabular data.
Avoid for v1. Black box. Hard to explain. Overkill here.
Recommended Approach (Phase by Phase):
Phase 1: Logistic Regression — fast baseline, sets minimum bar
Phase 2: Random Forest — captures non-linear patterns
Phase 3: XGBoost with SMOTE + hyperparameter tuning — production model
All three tracked in MLflow. Best model deployed.
## 7.3 Handling Class Imbalance
If your CRM has 35% Won and 65% Lost deals, a naive model will learn to always predict "Lost" and still get 65%
accuracy — which is useless for the business. Use all three strategies together:
- Strategy 1 — SMOTE: Creates synthetic Won deal examples in the training set (never test/validation). Interpolates
between real Won deals to balance classes to 50/50. Python: from imblearn.over_sampling import SMOTE
-  Strategy  2  —  Class  Weights:  XGBoost  parameter  scale_pos_weight  =  65/35  ≈  1.86.  The  model  penalises
misclassification of Won deals more heavily.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 19
## Confidential — For Personal Use Only
- Strategy 3 — Threshold Tuning: Default threshold of 0.5 is rarely optimal. Plot the Precision-Recall curve and find
the threshold that maximises business value — typically 0.35–0.40 to catch more Won deals early.
7.4 Evaluation Metrics — Business-Aligned
MetricWhat It MeasuresBusiness MeaningTarget
ROC-AUCDiscrimination across all
thresholds
How well the model separates Won vs Lost.
Best single summary metric.
## > 0.80
Precision (Won)TP / (TP + FP)Of deals I flag as likely wins — what % actually
win? Builds agent trust.
## > 0.70
Recall (Won)TP / (TP + FN)Of all actual wins — what % did I catch?
Prevents revenue leakage.
## > 0.65
F1 Score (Won)2 × P × R / (P + R)Balanced metric. Good when precision and
recall are both important.
## > 0.68
Log LossCross-entropy of
probabilities
Quality of probability calibration. Lower is
better.
## < 0.45
7.5 Why You Need a Business Cost Matrix
False Positive (Predict WIN, Actually LOST):
Agent wastes time on a deal that was not going to close anyway.
Estimated cost: 2 wasted agent days ≈ $1,000
False Negative (Predict LOSS, Actually WIN):
Deal gets deprioritised. Agent stops following up. Client goes cold.
On a $200K deal at 35% margin = $70,000 in lost profit.
CONCLUSION: False Negatives cost 50–70x more than False Positives.
Therefore: Lower your decision threshold to ~0.35 to catch more Won deals,
even if it means flagging a few more False Positives. This is a business decision.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 20
## Confidential — For Personal Use Only
## 08
Implementation Plan — Phase by Phase
## 8.1 Technology Stack
ComponentPurpose
SQL Server + SSISSource CRM data extraction — tools you already use at work
SnowflakeCloud data warehouse — all 3 medallion layers live here
dbt Core (free)All SQL transformations: staging, mart, and ML feature table
Python 3.10+EDA, model training, SHAP, batch scoring, Claude API calls
Key Python Librariespandas, scikit-learn, xgboost, shap, imbalanced-learn, mlflow
MLflow (free, local)Experiment tracking and model registry
VS CodePrimary IDE — install Python + dbt Power User extensions
Power BI DesktopDashboard — connects directly to Snowflake
Azure DevOps (Git)Version control for all dbt + Python code
Claude APIGenerates 3-sentence deal risk summaries per deal (GenAI layer)
## 8.2 Phase 1 — Environment Setup
-  Install  Python  3.10,  create  a  virtual  environment,  install:  pip  install  dbt-snowflake  mlflow  xgboost  shap
imbalanced-learn pandas scikit-learn anthropic
- Run dbt init sales_win_predictor. Configure profiles.yml with your Snowflake credentials (account, database,
warehouse, schema, role).
- Create Azure DevOps repository: sales-win-predictor. Commit the initial dbt project skeleton. First git push.
- Verify MLflow: run mlflow ui in terminal — you should see a local dashboard at localhost:5000.
## 8.3 Phase 2 — Data Generation & Bronze Layer
- Write a Python script to generate a synthetic CRM dataset: 600+ deals across 5 years, all 4 divisions, all 5 tables
(deals, line_items, agents, clients, stage_history). This gives you full control over the data for learning purposes.
- Load CSVs into SQL Server. Build SSIS packages for all 5 tables — same pattern as your existing pipelines. Add
an extracted_at Derived Column to each package.
- Validate row counts in Snowflake RAW schema. Verify incremental extraction logic works correctly (watermark on
LastModifiedDate).

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 21
## Confidential — For Personal Use Only
8.4 Phase 3 — dbt Silver & Gold Layer
-   Create   sources.yml   defining   the   RAW_CRM   schema.   Build   all   5   staging   models   (stg_crm_deals.sql,
stg_crm_agents.sql, etc.).
- Run dbt run --select staging. Fix any errors. Verify row counts match Bronze.
- Build intermediate models: int_agent_performance.sql (rolling 12m win rates), int_client_history.sql.
- Build all mart models. Add schema.yml tests for each (unique, not_null, relationships). Run dbt test — all tests
must pass.
- Build ml_deal_features.sql. Verify: one row per closed deal, no NULLs in target column, no leaking features.
## 8.5 Phase 4 — Exploratory Data Analysis
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# Load your feature table (export from Snowflake as CSV or use connector)
df = pd.read_csv("ml_deal_features.csv")
# Step 1: Check class balance
print(df["target"].value_counts(normalize=True))
## # Expected: Won ~35-45%, Lost ~55-65%
# Step 2: Win rate by division
df.groupby("vertical_clean")["target"].mean().sort_values().plot(kind="barh",
title="Win Rate by Division", color="#1D4ED8")
plt.tight_layout()
plt.savefig("win_rate_by_division.png")
# Step 3: Feature distributions - Won vs Lost (boxplots)
key_features = ["deal_value_log", "discount_pct",
## "total_days_in_funnel", "line_item_count"]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for i, col in enumerate(key_features):
df.boxplot(column=col, by="target",
ax=axes[i//2, i%2], grid=False)
# Step 4: Correlation heatmap - identify redundant features
sns.heatmap(df.select_dtypes("number").corr(),
cmap="coolwarm", center=0, annot=False)
plt.title("Feature Correlation Matrix")
## 8.6 Phase 5 — Model Training

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 22
## Confidential — For Personal Use Only
import xgboost as xgb
import mlflow
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report
from imblearn.over_sampling import SMOTE
# CRITICAL: Always use a CHRONOLOGICAL split — never random for deal data
train = df[df["deal_close_year"] <= 2022]
test = df[df["deal_close_year"] >= 2023]
## FEATURE_COLS = [
## "deal_value_log", "discount_pct", "line_item_count", "total_days_in_funnel",
## "days_in_negotiation", "num_contract_revisions", "agent_trailing_12m_win_rate",
## "agent_seniority_score", "client_historical_win_rate", "client_is_new",
"agent_current_workload", "competitor_flagged", # ... add all features
## ]
X_train, y_train = train[FEATURE_COLS], train["target"]
X_test, y_test = test[FEATURE_COLS], test["target"]
# Apply SMOTE only to TRAINING data — never to test data
sm = SMOTE(random_state=42)
X_train_sm, y_train_sm = sm.fit_resample(X_train, y_train)
# Train XGBoost with MLflow experiment tracking
with mlflow.start_run(run_name="xgboost_v1"):
model = xgb.XGBClassifier(
n_estimators=300,
learning_rate=0.05,
max_depth=5,
scale_pos_weight=1.86, # handles class imbalance
eval_metric="logloss",
random_state=42
## )
model.fit(X_train_sm, y_train_sm)
proba = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, proba)
mlflow.log_param("n_estimators", 300)
mlflow.log_metric("roc_auc", auc)
mlflow.xgboost.log_model(model, "sales_win_predictor_v1")
print(f"ROC-AUC: {auc:.4f}") # target: > 0.80

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 23
## Confidential — For Personal Use Only
## 09
## Deployment Strategy
9.1 Batch Prediction Pipeline (Recommended for v1)
For the first version, run predictions once per day in a batch pipeline. This is simpler to build, easier to debug, and
fully  sufficient  for  a  daily  sales  management  workflow.  The  model  scores  all  open  deals  every  morning  and  writes
results to a Snowflake table that Power BI reads.
n
TRIGGER — 2:00 AM Daily (SQL Server Agent)
SSIS packages run — CRM data extracted and landed in Snowflake Bronze
t
n
DBT RUN — 5:00 AM (Azure DevOps Pipeline or cron)
All dbt models refresh with latest CRM data. ml_deal_features updated.
t
n
## PYTHON SCORING — 6:00 AM
Load saved XGBoost model from MLflow. Score all OPEN deals. Compute SHAP values.
t
## -n
## GENAI SUMMARIES — 6:15 AM
Call Claude API for each deal. Write 3-sentence risk brief to Snowflake.
t
n
## POWER BI REFRESH — 7:00 AM
Scheduled dataset refresh. Agents see updated scores when they arrive at work.
9.2 ML Predictions Table (Snowflake — MART.ML_PREDICTIONS)
ColumnDescription
deal_idForeign key to dim_deal
prediction_dateDate these predictions were generated
model_versione.g. 'v1.2' — tracks which model scored this deal
win_probabilityFloat 0.0 to 1.0 (e.g. 0.724 = 72.4% chance of winning)
win_predictedBoolean — win_probability is above threshold (default 0.38)
probability_bandHIGH (above 70%) / MEDIUM (40–70%) / LOW (below 40%)
top_positive_factorTop SHAP feature pushing toward Win, in plain English
top_negative_factorTop SHAP feature pushing toward Loss, in plain English
ai_deal_summary3-sentence GenAI risk brief from Claude API

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 24
## Confidential — For Personal Use Only
## 9.3 Model Lifecycle
- Retrain Quarterly: Every 3 months, add last quarter's closed deals to training (expanding window). Keeps model
current.
- Performance Monitoring: After each batch run, compare predicted probabilities to actual outcomes for deals that
just closed. If ROC-AUC drops below 0.72 over 30 days, trigger a retrain.
- MLflow Model Registry: Register every trained model. Stages: None → Staging → Production → Archived. Never
overwrite production — always version.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 25
## Confidential — For Personal Use Only
## 10
Power BI Dashboard — Overview
The  Power  BI  dashboard  is  the  business  face  of  this  system.  It  connects  directly  to  Snowflake  and  reads  the
ML_PREDICTIONS table daily. The goal is to present AI scores in language a sales director can act on — not data
science jargon.
## Dashboard Pages Summary
## Pa
ge
NamePurposeKey Visuals
1Pipeline Command
## Centre
Daily overview — the first thing a
sales director opens each
morning.
KPI cards (pipeline value, weighted value, high/low probability
counts). Scatter plot: Deal Value vs Win Probability — the 4-quadrant
priority matrix.
2Deal Funnel AnalysisWhere are deals being lost in the
funnel?
Funnel chart (count + value at each stage). Win rate by division,
region, and month trend.
3Individual Deal
## Intelligence
Single-deal deep dive —
accessed by selecting any deal.
Win probability gauge (Red/Amber/Green). SHAP factor table.
AI-written deal summary card. Recommended actions banner.
4Agent PerformanceWho is performing well? Who
needs coaching?
Win rate per agent (bar chart). Workload vs win rate scatter. Avg
days to close.
5Client IntelligenceWhich client relationships are at
risk?
Win rate trend per client. Days since last deal. Lifetime value vs
recent activity.
6Revenue ForecastWhat revenue will realistically
close this quarter?
Probability-weighted pipeline (SUM of deal_value × win_probability).
High / Medium / Low confidence waterfall chart.
## Deal Priority Matrix — The Most Actionable Visual
Page 1's scatter plot creates four quadrants that tell agents exactly what to do:
QuadrantHigh/Low Value & ProbabilityAction for Agent
## Q1 — Top
## Right
HIGH Value + HIGH Probability (above
## 70%)
"Close Now" — assign best agent, push for signature this week.
## Q2 — Top
## Left
HIGH Value + LOW Probability (below
## 40%)
"Rescue Mission" — escalate to Director immediately. These are your
highest-risk, highest-cost deals.
## Q3 —
## Bottom
## Right
LOW Value + HIGH Probability (above
## 70%)
"Quick Wins" — close fast with minimal senior time. Good for junior agents.
## Q4 —
## Bottom Left
LOW Value + LOW Probability (below
## 40%)
"Consider Dropping" — evaluate whether agent time invested is justified.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 26
## Confidential — For Personal Use Only
Key DAX Measures
-- Win Rate (for any filter context: division, agent, region)
## Win Rate =
## DIVIDE(
COUNTROWS(FILTER(fact_deal_snapshot, [is_won] = 1)),
COUNTROWS(fact_deal_snapshot)
## )
-- Probability-Weighted Pipeline Value
-- This is more realistic than raw pipeline value
## Weighted Pipeline =
## SUMX(
ml_predictions,
RELATED(dim_deal[deal_value]) * [win_probability]
## )
-- Average Days to Close (Won deals only)
Avg Days to Close =
## AVERAGEX(
FILTER(dim_deal, [is_won] = 1),
## [total_days_in_funnel]
## )
## Snowflake Connection Setup
- In Power BI Desktop: Get Data → Snowflake → enter your account URL and warehouse name.
- Import mode (recommended for v1): All data loads into Power BI memory. Fast queries. Refresh daily.
- Tables to import: dim_deal, dim_client, dim_agent, dim_date, fact_deal_snapshot, ml_predictions.
- Set dim_date as your Date Table in Power BI (right-click table → Mark as date table).
- Schedule daily refresh after 7:00 AM so agents always see fresh scores.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 27
## Confidential — For Personal Use Only
## 11
## System Architecture
The diagram below shows the complete end-to-end system you will build. Everything in the blue/green shaded area is
work you already do at your job. The orange/purple area is new — this is what you are adding with this project.
End-to-End System Map
YOUR EXISTING WORK (Already familiar)
CRM SQL Servern Source system. All deal, agent, client, interaction data lives here.
SSIS Packagesn Daily incremental extraction. Bronze landing in Snowflake.
Snowflake — Bronzen Raw immutable tables. Never updated. Full history kept.
dbt — Silver/Goldn Staging models → Star Schema mart. Data quality tests.
Power BIn Dashboard connected to Snowflake. DAX measures.
NEW WORK YOU WILL ADD (This project)
dbt — ML Layern ml_deal_features.sql — final feature table for Python.
Python — EDAn Exploratory analysis: distributions, correlations, class balance.
Python — Trainingn XGBoost + SMOTE + MLflow. All experiments tracked.
Python — SHAPn Explainability layer. Feature importance per deal.
Python — Batch Scoringn Daily: score all open deals. Write to Snowflake ML_PREDICTIONS.
Claude APIn GenAI deal summaries. 3-sentence risk brief per deal.
## Data Flow Summary
n
CRM SQL Server → SSIS → Snowflake Bronze
Daily 2 AM: raw deal data lands as-is. Immutable.
t
n
dbt: Bronze → Silver → Gold → ML Layer
Daily 6 AM: clean, model, and compute all ML features.
t
n
Python: Load features → Train / Score → Write predictions
Daily 6:30 AM: XGBoost scores all open deals. SHAP explanations generated.
t

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 28
## Confidential — For Personal Use Only
## -n
Claude API: Deal summaries written to Snowflake
Daily 6:45 AM: 3-sentence AI risk brief per deal stored.
t
n
Power BI: Reads ML_PREDICTIONS → Dashboard refreshes
Daily 7 AM: agents see updated win probabilities and recommendations.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 29
## Confidential — For Personal Use Only
## 12
Advanced Features — SHAP, GenAI, Recommendations
12.1 SHAP Explainability
SHAP  (SHapley  Additive  exPlanations)  is  the  standard  method  for  explaining  tree-based  models  like  XGBoost.  It
assigns each feature a numerical value for each individual prediction — showing how much that feature pushed the
score toward Win (positive) or Loss (negative). This is what makes the model trustworthy to a sales director.
import shap
# Create explainer from your trained XGBoost model
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test) # shape: (n_deals, n_features)
## # --- GLOBAL PLOT ---
# Shows which features matter most across ALL deals
# Save as image for your portfolio
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
plt.savefig("shap_global_importance.png", bbox_inches="tight", dpi=150)
# --- WATERFALL PLOT (Individual Deal) ---
# Shows WHY a specific deal got its score
# Use deal index 0 as an example
shap.plots.waterfall(explainer(X_test)[0], show=False)
plt.savefig("shap_deal_0_waterfall.png", bbox_inches="tight", dpi=150)
# --- Extract top factors as text for Snowflake storage ---
deal_shap = shap_values[0] # SHAP values for deal index 0
feature_names = X_test.columns.tolist()
# Sort by absolute SHAP value
sorted_idx = abs(deal_shap).argsort()[::-1]
top_positive = [(feature_names[i], deal_shap[i])
for i in sorted_idx if deal_shap[i] > 0][:3]
top_negative = [(feature_names[i], deal_shap[i])
for i in sorted_idx if deal_shap[i] < 0][:3]
print("Top factors FOR winning:", top_positive)
print("Top factors AGAINST winning:", top_negative)
Converting SHAP Values to Business Language
Raw SHAP numbers (e.g. 0.34, -0.18) mean nothing to a sales agent. Build a function that converts them into plain
sentences:

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 30
## Confidential — For Personal Use Only
def shap_to_english(feature_name, shap_value, feature_value):
## """
Converts a SHAP value into a plain English explanation.
shap_value > 0 means the feature pushed toward WIN.
shap_value < 0 means the feature pushed toward LOSS.
## """
direction = "pos" if shap_value > 0 else "neg"
templates = {
## "agent_trailing_12m_win_rate": {
"pos": f"Agent has a strong {feature_value:.0%} win rate this year — positive signal",
"neg": f"Agent has a low {feature_value:.0%} win rate this year — risk factor"
## },
## "total_days_in_funnel": {
"pos": f"Deal moving fast at {feature_value:.0f} days — below historical average",
"neg": f"Deal is stale at {feature_value:.0f} days — average is 45 days for similar deals"
## },
## "discount_pct": {
"pos": f"Discount of {feature_value:.0%} is within the safe range",
"neg": f"Discount of {feature_value:.0%} is above the 20% safety threshold"
## },
## "line_item_count": {
"pos": f"Lean deal with {feature_value:.0f} line items — easier to close",
"neg": f"Complex deal with {feature_value:.0f} line items — high negotiation surface"
## },
# Add all features here...
## }
return templates.get(feature_name, {}).get(
direction, f"{feature_name}: {shap_value:.3f}"
## )
## 12.2 Recommendation Engine
The recommendation engine answers a specific question for each deal: "What is the single most impactful action the
agent can take right now to increase the win probability?" It is built on the SHAP output.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 31
## Confidential — For Personal Use Only
Example Output — Footwear Brand Licensing Deal (Win Probability: 34%)
Recommendation 1 [Estimated impact: +12 percentage points]
Current discount: 31%. Deals with discount below 20% in Licensing win at 58% vs 22%.
Action: Work with the client to reduce scope (remove APAC usage rights) to justify
bringing the discount below 20% without reducing the Minimum Guarantee value.
Recommendation 2 [Estimated impact: +8 percentage points]
Assigned agent has a 28% Licensing win rate. Team specialist has 51%.
Action: Bring the BrandVault licensing specialist into the next client call.
Recommendation 3 [Estimated impact: +6 percentage points]
Deal in Negotiation for 24 days. Average winning deal exits Negotiation in 12 days.
Action: Set a firm 5-business-day deadline with client. Offer a minor concession.
12.3 GenAI Deal Summaries — Claude API
For  each  open  deal,  the  batch  pipeline  calls  the  Claude  API  once  per  day  and  stores  the  response  in  Snowflake.
Power BI displays it as a text card on the Individual Deal Intelligence page.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 32
## Confidential — For Personal Use Only
import anthropic
client = anthropic.Anthropic() # reads ANTHROPIC_API_KEY from environment
def generate_deal_summary(deal: dict) -> str:
## """
Generates a 3-sentence deal risk brief for one deal.
deal = a dictionary of deal features + SHAP factors from Snowflake.
## """
prompt = f"""
You are an expert sales coach at a global talent and brand company.
Write a 3-sentence deal intelligence brief for a sales agent.
Use specific numbers. Recommend one clear action. Professional tone.
## Deal Name: {deal["deal_name"]}
## Division: {deal["vertical"]}
## Deal Value: ${deal["deal_value"]:,.0f}
## Win Probability: {deal["win_probability"]:.0%}
Days in Pipeline:{deal["total_days_in_funnel"]}
## Key Risk: {deal["top_negative_factor"]}
## Key Positive: {deal["top_positive_factor"]}
## """
response = client.messages.create(
model="claude-sonnet-4-20250514",
max_tokens=200,
messages=[{"role": "user", "content": prompt}]
## )
return response.content[0].text
# In your batch scoring loop:
# for deal in open_deals:
# deal["ai_summary"] = generate_deal_summary(deal)
# Then write deal["ai_summary"] to MART.ML_PREDICTIONS in Snowflake.
Example GenAI Output — Footwear Brand Campaign (Win Probability: 34%)
"This deal is at significant risk due to a 31% discount — well above the 20% ceiling
where win probability drops sharply on Marketing campaigns of this size — combined
with 24 days of stalled negotiation, nearly double the average for comparable deals.
The strongest positive signal is the client's two prior won campaigns with PulseMedia,
confirming genuine intent to work together.
This week, the agent should propose a scope reduction to bring the discount under 18%
and set a firm close deadline to re-establish commercial momentum."

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 33
## Confidential — For Personal Use Only
## 13
## Learning Roadmap
You have a strong foundation: SQL, SSIS, dbt, Snowflake, Power BI, Azure DevOps. You are not starting from zero
— you are extending your existing data engineering skills into ML territory. The gaps are specific and completeable in
4 weeks. Here is exactly what to learn, in what order, and why it matters for this project.
Week 1 — Python for Data (if not yet fluent)
TopicWhat to LearnWhy for This ProjectBest Resource
pandasDataFrame, groupby, merge,
pivot, fillna, apply
80% of EDA and feature prep is
pandas
pandas.pydata.org → Getting Started
numpyArrays, log transform, np.log1p()deal_value_log feature computationnumpy.org → quickstart
matplotlib +
seaborn
barh, boxplot, heatmapEDA: visualise Win vs Lost
distributions
seaborn.pydata.org → gallery
Week 1–2 — Core ML Concepts (Understand, Not Just Use)
ConceptPlain English ExplanationWhy It Matters Here
Bias-Variance TradeoffComplex models memorise training data
(overfit). Simple models miss patterns
(underfit). Balance is the goal.
Drives every XGBoost hyperparameter decision you make.
Train / Test SplitYou can only evaluate a model on data it
has never seen during training. Otherwise
the score is fake.
Must use chronological split (not random) for deal data.
Precision vs RecallPrecision: when I predict Win, am I right?
Recall: did I find all the actual Wins?
False Negatives cost far more. Tune threshold toward higher
recall.
ROC-AUC ScoreHow well the model separates Won from
Lost deals across all possible thresholds.
Your primary evaluation metric. Target above 0.80.
Data LeakageUsing information that would not be
available at prediction time. Gives falsely
optimistic results.
The single most common ML mistake. This project trains you to
avoid it.
Week 2–3 — sklearn + XGBoost + SMOTE
Library / ToolKey Things to LearnProject Application
scikit-learn PipelineSimpleImputer, StandardScaler,
ColumnTransformer, Pipeline.fit/predict
Prevents leakage. Enables clean cross-validation. Industry
standard.
XGBoostn_estimators, learning_rate, max_depth,
scale_pos_weight, eval_metric
Your production model. Must understand every
hyperparameter.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 34
## Confidential — For Personal Use Only
RandomizedSearchCVHow to tune 50+ combinations efficiently vs
brute-force GridSearchCV
Week 3: squeeze ROC-AUC from 0.77 to 0.83+ with tuning.
imbalanced-learn SMOTEHow synthetic oversampling works. Why
apply only to training data.
Fix the 65/35 class imbalance in your deal dataset.
Week 3–4 — SHAP + MLflow + Claude API
ToolWhat to LearnProject Application
SHAPTreeExplainer, shap_values,
summary_plot, waterfall, force_plot
Explain every prediction in plain English for Power BI.
MLflow Trackingmlflow.log_param, log_metric, log_model,
start_run
Track all experiments. Never lose a result or model version.
MLflow Registryregister_model,
transition_model_version_stage
Deploy model cleanly. Enable quarterly retraining cycle.
Anthropic Claude APImessages.create, prompt engineering,
parse response content
Auto-generate deal risk summaries for every open deal daily.
Interview Questions You Must Be Able to Answer
QuestionAnswer to Memorise
Why chronological train/test split?Deals in 2023 are influenced by market dynamics that didn't exist in 2020. Random split
lets future information leak into training — giving falsely high accuracy that collapses in
production.
What is data leakage?Using features that would only be known after the outcome occurs. Example: including
actual_close_date in training would perfectly predict is_won — but you'd never have that
date at prediction time.
Why XGBoost over a Neural Net?Tabular CRM data with under 100K rows — tree models always outperform. XGBoost is
interpretable with SHAP, faster to train, and easier to debug.
What is SMOTE doing?Creates synthetic Won deal examples by interpolating between real ones in feature
space. Applied only to training data — never test. Fixes the 65/35 class imbalance.
Why a snapshot table?Captures deal state at each stage transition, not just final outcome. Lets you train on
"what the deal looked like at Negotiation entry" — when there is still time to act.
How do you monitor model drift?Compare predicted win probability distribution to actual outcomes for newly closed deals.
Monthly: recompute ROC-AUC on the last 90 days. Threshold alert at 0.72 triggers a
retrain.

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 35
## Confidential — For Personal Use Only
## 14
4-Week Day-by-Day Execution Plan
This is your solo build plan. Every day has one concrete deliverable. At the end of 28 days you will have a working,
portfolio-ready AI system. Do not skip days. Do not rush. Understand every line you write.
WEEK 1 — Foundation: Environment + Data
DayTasksDeliverable
## Day
## 1
Install Python 3.10, VS Code (Python + dbt extensions), dbt Core, MLflow,
XGBoost, SHAP, imbalanced-learn, anthropic. Create Azure DevOps repo. First
commit.
Working dev environment
## Day
## 2
Write Python script to generate synthetic CRM dataset: 600 deals, 5 years, all 4
divisions. Output 5 CSVs: deals, line_items, agents, clients, stage_history.
Synthetic dataset ready
## Day
## 3
Load CSVs into SQL Server. Build SSIS package for deals table (full load).
Validate row count in Snowflake RAW schema.
raw_crm_deals in Snowflake
## Day
## 4
Build remaining 4 SSIS packages. Add extracted_at Derived Column to each.
Run all packages. Verify 5 Bronze tables.
All 5 Bronze tables loaded
## Day
## 5
dbt init. Configure profiles.yml. Create sources.yml. Build stg_crm_deals.sql. Run
dbt run. Fix any errors.
First dbt model running
## Day
## 6
Build remaining 4 staging models. Add schema.yml tests (unique, not_null). Run
dbt test — all pass.
All staging models validated
## Day
## 7
Review and clean Week 1 work. Update README.md. Push clean branch to
Azure DevOps.
Week 1 documented in git
WEEK 2 — dbt Gold Layer + Feature Engineering
DayTasksDeliverable
## Day
## 8
Build dim_deal, dim_client, dim_agent, dim_date in dbt mart layer. Verify joins
and row counts.
4 dimension tables done
## Day
## 9
Build fact_deal_snapshot (snapshot logic) and fact_line_items. Add referential
integrity tests.
Core fact tables done
## Day
## 10
Build int_agent_performance.sql (rolling 12m win rate) and int_client_history.sql.Agent + client metrics ready
## Day
## 11
Build ml_deal_features.sql. Join all tables. Compute derived metrics: velocity
score, discount_risk_score, engagement score.
ML feature table complete
## Day
## 12
Python EDA: load feature table, check class balance, win rate by division/region,
boxplots (Won vs Lost), correlation heatmap. Save 8+ plots.
EDA notebook with visuals

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 36
## Confidential — For Personal Use Only
## Day
## 13
Document missing value strategy per column. Verify zero data leakage in feature
table. Create feature inventory list with business hypothesis for each.
Feature inventory doc done
## Day
## 14
Full dbt test suite run — zero failures. Merge all branches. Clean up SQL
comments.
Tested, clean dbt project
WEEK 3 — ML Model + SHAP + GenAI
DayTasksDeliverable
## Day
## 15
Build sklearn preprocessing Pipeline (imputer + scaler + encoder). Train Logistic
Regression baseline. Log to MLflow. Record ROC-AUC.
Baseline model logged
## Day
## 16
Train Random Forest with default params. Compare to baseline in MLflow. Plot
feature importances.
RF model in MLflow
## Day
## 17
Train XGBoost baseline. Apply SMOTE to training data. Compare all 3 models in
MLflow UI.
Best model selected
## Day
## 18
XGBoost hyperparameter tuning with RandomizedSearchCV — 50 iterations. Log
all runs to MLflow.
Tuned XGBoost — target AUC > 0.80
## Day
## 19
Threshold optimisation: plot Precision-Recall curve. Choose business-optimal
threshold. Register best model in MLflow Model Registry.
Model registered in MLflow
## Day
## 20
SHAP: summary_plot (global), waterfall plots for 3 deals (Win / Loss / Borderline).
Build shap_to_english() function.
SHAP + English converter done
## Day
## 21
Build batch scoring script. Test Claude API with 3 deals. Write
ML_PREDICTIONS + ML_DEAL_SUMMARIES to Snowflake.
Scoring pipeline functional
WEEK 4 — Power BI + Polish + Portfolio
DayTasksDeliverable
## Day
## 22
Connect Power BI to Snowflake. Import 6 tables. Build relationships. Create all
DAX measures (Win Rate, Weighted Pipeline, Avg Days to Close).
Power BI data model done
## Day
## 23
Build Page 1 (Pipeline Command Centre: KPI cards + scatter plot) and Page 2
(Deal Funnel Analysis).
Pages 1–2 complete
## Day
## 24
Build Page 3 (Individual Deal Intelligence: gauge + SHAP table + AI summary +
recommendations) and Page 4 (Agent Performance).
Pages 3–4 complete
## Day
## 25
Build Page 5 (Client Intelligence) and Page 6 (Revenue Forecast with
probability-weighted pipeline).
All 6 pages complete
## Day
## 26
End-to-end integration test: SSIS run → dbt run → Python scoring → Power BI
refresh. Fix any issues. Time the full pipeline.
Full pipeline tested E2E
## Day
## 27
Create architecture diagram in draw.io. Write full README.md. Add code
comments to all Python files. Create requirements.txt.
Portfolio documentation done

Sales Win Predictor  |  Project Specification  |  Solo Build GuidePage 37
## Confidential — For Personal Use Only
## Day
## 28
Record a 5-minute screen walkthrough video. Write 10 interview Q&A; answers
based on the "Learning Roadmap" section. Apply to 3 target roles.
Portfolio-ready. Job search begins.
## Final Word — This Project Is Your Turning Point.
You mentioned your job is at risk. Here is what this project gives you:
After Day 28 you will have:
n Built a full AI system end-to-end — raw SQL to deployed ML to Power BI
n Deep domain knowledge in CRM-driven sales organisations
n Hands-on experience with every tool interviewers ask about
n A git repo you can walk through in any interview
n Real answers to real ML questions — because you lived through them
Do not rush it. Do not skip sections.
Build every line yourself. That is how this changes your career.