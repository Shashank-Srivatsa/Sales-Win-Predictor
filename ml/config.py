"""
config.py — Single source of truth for the entire ML pipeline.

Every other script imports from here. Changing something once (e.g., adding a feature)
automatically propagates to training, scoring, and evaluation.
"""

import os
import pathlib
from dotenv import load_dotenv

# Load SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD from the project .env file.
# os.path.dirname(__file__) = the ml/ folder; ../  goes one level up to the project root.
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Snowflake connection ──────────────────────────────────────────────────────
# The ML schema holds our feature table and predictions.
# Never hard-code passwords — they come from the .env file only.
SNOWFLAKE_CONFIG = {
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": "COMPUTE_WH",
    "database":  "SALES_WIN_DB",
    "schema":    "ML",
}

# ── MLflow experiment tracking ────────────────────────────────────────────────
# MLflow records every training run locally in the ml/ folder.
# This means you can compare "run from last week" vs "run today" at any time.
# pathlib.as_uri() converts C:\...\mlflow_runs -> file:///C:/.../mlflow_runs
# which MLflow requires on Windows (it rejects raw Windows paths).
MLFLOW_TRACKING_URI = pathlib.Path(
    os.path.join(os.path.dirname(__file__), "mlflow_runs")
).as_uri()
EXPERIMENT_NAME     = "sales_win_predictor"
MODEL_NAME          = "xgboost_win_predictor"

# ── Feature columns fed to XGBoost ───────────────────────────────────────────
# IMPORTANT: 'deal_value_raw' is intentionally excluded.
#   - We use 'deal_value_log' instead because deal values are right-skewed
#     (most deals $10k–$50k, a few outliers at $500k+). Log compression gives
#     XGBoost better split quality in the upper tail.
#   - 'opportunity_id', 'opportunity_sk', 'fiscal_year', etc. are identifiers,
#     not signals — including them would cause the model to memorise row IDs.
FEATURE_COLS = [
    # [A] Deal Value
    "deal_value_log",           # LN(amount + 1) — compressed deal size
    "discount_pct",             # 0–100 — how much was discounted
    "discount_risk_score",      # 0–4 ordinal — buckets the discount into risk tiers
    "deal_size_relative_to_client_avg",  # Is this deal bigger or smaller than usual for this client?

    # [B] Deal Categorical (label-encoded — XGBoost needs numbers, not strings)
    "deal_type_encoded",        # 0=New, 1=Renewal, 2=Upsell, 3=Cross-sell
    "division_encoded",         # 0=TalentEdge … 3=BrandVault
    "region_encoded",           # 0=NA, 1=EU, 2=IN, 3=APAC, 4=AU
    "is_renewal",               # 1/0 flag — renewals win at ~2x the rate of new business

    # [C] Deal Timing
    "total_days_in_funnel",     # How long has this deal been alive?
    "days_in_negotiation_stage",# KEY: >21 days in negotiation = strong loss signal
    "days_in_opportunity_stage",
    "created_month",            # Quarter-end months (3,6,9,12) close at higher rates
    "is_fiscal_quarter_end_period",  # 1 if deal was created in last 14 days of a quarter

    # [D] Deal Complexity
    "line_item_count",          # More line items = more moving parts = harder to close
    # deal_complexity_score DROPPED — r=0.96 with line_item_count (pure redundancy, found in EDA)
    "has_usage_rights",         # 1 = deal includes Usage Rights (common in BrandVault)
    "has_minimum_guarantee",    # 1 = Minimum Guarantee clause (BrandVault specific)

    # [E] Velocity
    "deal_velocity_score",      # median_days_for_division / actual_days — >1 = moving fast

    # [F] Agent
    "agent_trailing_12m_win_rate",   # Agent's recent form — most predictive agent feature
    "agent_seniority_level",         # 1=Junior … 5=VP
    "agent_current_open_deals",      # >30 open deals → win rate drops
    "agent_win_rate_this_division",  # Win rate specifically in THIS deal's division
    "is_vertical_specialist",        # 1 if agent's home division matches deal's division

    # [G] Client
    "client_win_rate",          # How often does this client buy from us?
    "client_is_new",            # 1 = first deal ever with this client
    "client_days_since_last_deal",   # Long gap = cooler relationship
    "account_tier",             # 1=top client, 2=mid, 3=small/new

    # [H] Engagement
    "total_activities",         # Emails + calls + meetings on this deal
    "days_since_last_activity", # Silence = disengagement signal
    "engagement_score",         # activities_last_14_days / total (recency-weighted)
    "positive_activity_ratio",  # positive_outcomes / total_activities

    # [I] Negotiation Risk
    "stage_regression_count",   # Times the deal moved *backwards* in the funnel
    "contract_revision_count",  # Contract redrafts before signing — friction signal
]

TARGET_COL = "target_is_won"   # 1=Won, 0=Lost, NULL=still open (never fill NULLs)
ID_COL     = "opportunity_id"

# ── Training hyperparameters ──────────────────────────────────────────────────
# EARLY_STOPPING_ROUNDS: if test-set logloss doesn't improve for 30 consecutive
# trees, stop training. Better than fixing n_estimators=400 because:
#   - Prevents overfitting (model stops when it starts memorising training data)
#   - Faster training (usually converges at 80–150 trees, not 400)
EARLY_STOPPING_ROUNDS = 30
N_ESTIMATORS_MAX      = 1000   # upper bound — early stopping will kick in before this

# ── Decision threshold (will be tuned in 03_evaluate.py) ─────────────────────
# The model outputs a probability (0–1). We convert it to a yes/no prediction
# by comparing to this threshold. 0.5 is NOT the right default here because:
#   - Losing a deal we predicted as "win" (False Negative) costs the business
#     roughly 50x more than misclassifying a lost deal as "lost" (False Positive)
#   - Lower threshold = model predicts "win" more aggressively = fewer missed wins
# 03_evaluate.py will compute the optimal value from the data.
# This is a fallback default only.
DECISION_THRESHOLD = 0.38

# ── Output directories (created by scripts that need them) ───────────────────
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
