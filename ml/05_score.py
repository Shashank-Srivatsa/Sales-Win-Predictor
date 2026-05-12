"""
05_score.py — Score All Open Deals

PURPOSE:
  Apply the trained model to every open deal (ml_split = 'score').
  For each deal we produce:
    - win_probability   : a number between 0 and 1
    - win_predicted     : True/False based on the tuned threshold
    - probability_band  : HIGH / MEDIUM / LOW (for Power BI colour coding)
    - top_positive_factors : top 3 SHAP features pushing TOWARD Won
    - top_negative_factors : top 3 SHAP features pushing TOWARD Lost

LEARNING NOTE — Why score separately from training?
  Training is expensive (minutes) and only needs to happen when:
    - new data arrives (e.g., a full quarter of new closed deals)
    - you want to try different features or hyperparameters
  Scoring is cheap (seconds) and runs DAILY on the 48 currently open deals.
  Separating these two steps is standard MLOps practice.

OUTPUT:
  ml/predictions_staging.csv   -- inspectable before writing to Snowflake
  Console: summary table of all scored deals

HOW TO RUN:
  python ml/05_score.py
"""

import os, sys, warnings, datetime
warnings.filterwarnings('ignore')

import snowflake.connector
import pandas as pd
import numpy as np
import shap
import mlflow
import mlflow.xgboost
from mlflow.tracking import MlflowClient

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL, ID_COL,
    MLFLOW_TRACKING_URI, MODEL_NAME,
)

print("=" * 60)
print("  SALES WIN PREDICTOR -- Scoring Open Deals")
print("=" * 60)


# ── 1. Load model + threshold ─────────────────────────────────────────────────
print("\n[1/4] Loading model and tuned threshold...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client   = MlflowClient()
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
if not versions:
    raise RuntimeError("No trained model found. Run 02_train.py first.")

latest       = sorted(versions, key=lambda v: int(v.version), reverse=True)[0]
model        = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{latest.version}")
model_version = f"v{latest.version}"

# Read the threshold chosen by 03_evaluate.py — never hardcode it here
threshold_path = os.path.join(os.path.dirname(__file__), "best_threshold.txt")
if not os.path.exists(threshold_path):
    raise RuntimeError("best_threshold.txt not found. Run 03_evaluate.py first.")

with open(threshold_path) as f:
    THRESHOLD = float(f.read().strip())

print(f"  Model     : {MODEL_NAME}  {model_version}")
print(f"  Threshold : {THRESHOLD}  (loaded from best_threshold.txt)")


# ── 2. Load open deals ────────────────────────────────────────────────────────
# LEARNING NOTE:
#   ml_split = 'score' corresponds to is_open = 1 in fact_opportunities.
#   These deals have no is_won label (target_is_won IS NULL) — we don't know
#   the outcome yet. The model's job is to estimate the probability of winning.

print("\n[2/4] Loading open deals from Snowflake...")

conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df = pd.read_sql(
    """
    SELECT *
    FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
    WHERE ML_SPLIT = 'score'
    ORDER BY OPPORTUNITY_ID
    """,
    conn,
)
conn.close()

df.columns = df.columns.str.lower()
feat_cols  = [f for f in FEATURE_COLS if f in df.columns]
X_score    = df[feat_cols]

print(f"  Open deals to score : {len(df):,}")
print(f"  Features used       : {len(feat_cols)}")


# ── 3. Predict probabilities ──────────────────────────────────────────────────
# LEARNING NOTE — what predict_proba returns:
#   model.predict_proba(X) -> 2D array, shape (n_deals, 2)
#   Column 0 = probability of Lost,  Column 1 = probability of Won
#   Both columns always sum to 1.0 for each row.
#   We take [:, 1] to get the "Won" probability for every deal.

print("\n[3/4] Running predictions + SHAP explanations...")

proba = model.predict_proba(X_score)[:, 1]

# Assign probability bands for Power BI colour coding
# HIGH = deal is likely to close (green in Power BI)
# MEDIUM = uncertain — needs attention (amber)
# LOW = deal is at risk (red — "rescue" quadrant)
def assign_band(p):
    if p >= 0.70:  return "HIGH"
    if p >= 0.40:  return "MEDIUM"
    return "LOW"

# Compute SHAP for every open deal
# We reuse the same TreeExplainer approach from 04_explain.py
explainer   = shap.TreeExplainer(model)
explanation = explainer(X_score)
shap_vals   = explanation.values
if shap_vals.ndim == 3:
    shap_vals = shap_vals[:, :, 1]   # take class-1 (Won) SHAP values

# top_shap_factors — same logic as in 04_explain.py (redefined here to avoid
# importing from a file whose name starts with a digit, which Python disallows)
def top_shap_factors(shap_row, feature_names, n=3):
    sorted_idx = np.argsort(np.abs(shap_row))[::-1]
    positive   = [feature_names[i] for i in sorted_idx if shap_row[i] > 0][:n]
    negative   = [feature_names[i] for i in sorted_idx if shap_row[i] < 0][:n]
    return ", ".join(positive), ", ".join(negative)

pos_factors_list = []
neg_factors_list = []

for i in range(len(X_score)):
    pos, neg = top_shap_factors(shap_vals[i], feat_cols, n=3)
    pos_factors_list.append(pos)
    neg_factors_list.append(neg)

today = datetime.date.today()

results = pd.DataFrame({
    "OPPORTUNITY_ID"       : df[ID_COL].values,
    "PREDICTION_DATE"      : today,
    "MODEL_VERSION"        : model_version,
    "WIN_PROBABILITY"      : np.round(proba, 6),
    "WIN_PREDICTED"        : proba >= THRESHOLD,
    "PROBABILITY_BAND"     : [assign_band(p) for p in proba],
    "TOP_POSITIVE_FACTORS" : pos_factors_list,
    "TOP_NEGATIVE_FACTORS" : neg_factors_list,
    "SCORED_AT"            : pd.Timestamp.utcnow(),
})

# ── 4. Print summary and save ─────────────────────────────────────────────────
band_counts = results["PROBABILITY_BAND"].value_counts()
won_count   = results["WIN_PREDICTED"].sum()

print(f"\n  Scored {len(results):,} open deals")
print(f"  Predicted Won  : {won_count}  (threshold >= {THRESHOLD})")
print(f"  Predicted Lost : {len(results) - won_count}")
print(f"\n  Probability bands:")
for band in ["HIGH", "MEDIUM", "LOW"]:
    n = band_counts.get(band, 0)
    bar = "#" * n
    print(f"    {band:<8}: {n:>3}  {bar}")

print(f"\n  Deal-level predictions:")
print(f"\n  {'Opportunity':<14} {'Prob':>6}  {'Band':<8} {'Predicted':<10} {'Top Win Drivers'}")
print(f"  {'-'*14} {'-'*6}  {'-'*8} {'-'*10} {'-'*45}")

for _, row in results.sort_values("WIN_PROBABILITY", ascending=False).iterrows():
    pred_label = "WIN" if row["WIN_PREDICTED"] else "loss"
    print(
        f"  {row['OPPORTUNITY_ID']:<14} "
        f"{row['WIN_PROBABILITY']:>6.3f}  "
        f"{row['PROBABILITY_BAND']:<8} "
        f"{pred_label:<10} "
        f"{row['TOP_POSITIVE_FACTORS']}"
    )

# Save to staging CSV so you can inspect before writing to Snowflake
staging_path = os.path.join(os.path.dirname(__file__), "predictions_staging.csv")
results.to_csv(staging_path, index=False)
print(f"\n  Saved -> ml/predictions_staging.csv  (inspect before writing to Snowflake)")

print("\n" + "=" * 60)
print("  SCORING COMPLETE")
print("=" * 60)
print(f"  Open deals scored   : {len(results)}")
print(f"  Predicted wins      : {won_count}  ({won_count/len(results)*100:.0f}%)")
print(f"  HIGH confidence     : {band_counts.get('HIGH', 0)}")
print(f"  MEDIUM confidence   : {band_counts.get('MEDIUM', 0)}")
print(f"  LOW / at-risk       : {band_counts.get('LOW', 0)}")
print()
print("  NEXT STEP: run ml/06_write_predictions.py  (commit to Snowflake)")
print("=" * 60)
