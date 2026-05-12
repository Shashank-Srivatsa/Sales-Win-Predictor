"""
04_explain.py — SHAP Explainability

PURPOSE:
  XGBoost is a "black box" — it gives you a prediction but not a reason.
  SHAP (SHapley Additive exPlanations) opens the box: for every deal, it
  tells you WHICH features pushed the prediction up (toward Won) and which
  pushed it down (toward Lost), and by HOW MUCH.

KEY LEARNING CONCEPTS IN THIS FILE:
  1. What SHAP is and why it is better than feature importance
  2. Global vs local explanations
  3. How to read a SHAP waterfall chart
  4. The base value — what the model predicts before seeing any features
  5. top_shap_factors() — the helper 05_score.py will use for every open deal

OUTPUTS:
  ml/plots/08_shap_global_bar.png      -- which features matter most overall
  ml/plots/09_shap_beeswarm.png        -- direction of each feature's effect
  ml/plots/10_shap_waterfall_wonex.png -- breakdown for one Won deal
  ml/plots/11_shap_waterfall_lostex.png-- breakdown for one Lost deal
  Console: ranked feature importance table

HOW TO RUN:
  python ml/04_explain.py
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import snowflake.connector
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')   # non-interactive backend — saves to file, no pop-up needed
import matplotlib.pyplot as plt
import shap
import mlflow
import mlflow.xgboost
from mlflow.tracking import MlflowClient

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL,
    MLFLOW_TRACKING_URI, MODEL_NAME, EXPERIMENT_NAME, PLOTS_DIR,
)

os.makedirs(PLOTS_DIR, exist_ok=True)

print("=" * 60)
print("  SALES WIN PREDICTOR -- SHAP Explainability")
print("=" * 60)


# ── 1. What is SHAP? (read before looking at the code) ───────────────────────
# LEARNING NOTE:
#
#   Imagine the model's prediction as a starting point (the "base value") — the
#   average win probability across ALL training deals. For each deal, every feature
#   either INCREASES or DECREASES the prediction from that starting point.
#
#   SHAP measures exactly how much each feature contributed, in probability units.
#   Example for deal OPP-4521 (base value = 0.73):
#
#     agent_trailing_12m_win_rate  : +0.18  (agent has been on a hot streak)
#     days_in_negotiation_stage    : -0.12  (deal has been stuck 28 days)
#     discount_pct                 : -0.08  (28% discount is a red flag)
#     client_win_rate              : +0.05  (client usually buys from us)
#     ... 28 more features ...
#     ----------------------------------------
#     Final prediction             :  0.76  (73% + sum of all pushes)
#
#   The key advantage over "feature importance":
#     - Feature importance: "discount_pct matters a lot globally"
#     - SHAP:              "for THIS deal, discount_pct is pushing the prediction
#                           DOWN by 0.08 because it's 28% (above the risky 20% rule)"
#   SHAP is per-deal, directional, and in the same units as the prediction.


# ── 2. Load model and test data ───────────────────────────────────────────────
print("\n[1/4] Loading model and test data...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient()
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
latest   = sorted(versions, key=lambda v: int(v.version), reverse=True)[0]
model    = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{latest.version}")

conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df = pd.read_sql(
    """
    SELECT *
    FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
    WHERE ML_SPLIT = 'test'
    ORDER BY FISCAL_YEAR, OPPORTUNITY_ID
    """,
    conn,
)
conn.close()

df.columns = df.columns.str.lower()
feat_cols  = [f for f in FEATURE_COLS if f in df.columns]
X_test     = df[feat_cols]
y_test     = df[TARGET_COL].astype(int)

print(f"  Model  : {MODEL_NAME}  version {latest.version}")
print(f"  Test   : {len(X_test):,} deals  ({feat_cols.__len__()} features)")


# ── 3. Compute SHAP values ────────────────────────────────────────────────────
# LEARNING NOTE:
#   TreeExplainer is a fast, exact SHAP algorithm designed for tree-based models
#   (decision trees, random forests, XGBoost, LightGBM).
#   For neural networks you would use DeepExplainer or GradientExplainer instead.
#
#   explainer(X_test) returns an Explanation object containing:
#     .values      -- SHAP values, shape (n_deals, n_features)
#                     positive = pushed prediction TOWARD Won
#                     negative = pushed prediction TOWARD Lost
#     .base_values -- the starting probability before any features (same for all deals)
#     .data        -- the actual feature values for each deal

print("\n[2/4] Computing SHAP values (TreeExplainer)...")

explainer   = shap.TreeExplainer(model)
explanation = explainer(X_test)

shap_vals = explanation.values

# For binary XGBoost, SHAP may return 3D (n_samples, n_features, 2).
# We only want the values for class 1 (Won).
if shap_vals.ndim == 3:
    shap_vals = shap_vals[:, :, 1]
    explanation_1d = shap.Explanation(
        values       = shap_vals,
        base_values  = explanation.base_values[:, 1] if explanation.base_values.ndim > 1
                       else explanation.base_values,
        data         = explanation.data,
        feature_names= feat_cols,
    )
else:
    explanation_1d = shap.Explanation(
        values       = shap_vals,
        base_values  = explanation.base_values,
        data         = explanation.data,
        feature_names= feat_cols,
    )

base_val = float(np.mean(explanation_1d.base_values))
print(f"  Base value (avg predicted probability) : {base_val:.4f}")
print(f"  This is the model's prediction BEFORE looking at any features.")
print(f"  Every feature then pushes the prediction up or down from {base_val:.2f}.")


# ── 4. Global feature importance ──────────────────────────────────────────────
# LEARNING NOTE:
#   Global importance = mean(|SHAP value|) across all test deals.
#   It answers: "which features move the prediction the most, on average?"
#   This does NOT tell you the direction — just the magnitude.
#   The beeswarm plot (next section) shows direction.

mean_abs_shap = pd.Series(
    np.abs(shap_vals).mean(axis=0),
    index=feat_cols,
).sort_values(ascending=False)

print("\n[3/4] Global feature importance (mean |SHAP|):")
print(f"\n  {'Rank':<5} {'Feature':<40} {'Mean |SHAP|'}")
print(f"  {'-'*5} {'-'*40} {'-'*12}")
for rank, (feat, val) in enumerate(mean_abs_shap.items(), 1):
    bar = "#" * int(val * 200)   # rough ASCII bar
    print(f"  {rank:<5} {feat:<40} {val:.5f}  {bar}")


# ── 5. Save SHAP plots ────────────────────────────────────────────────────────
print("\n[4/4] Saving SHAP plots...")

# Plot A — Global bar chart (mean |SHAP| per feature)
plt.figure(figsize=(10, 8))
shap.plots.bar(explanation_1d, max_display=20, show=False)
plt.title("Global Feature Importance (mean |SHAP| on test set)", fontsize=12, pad=12)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "08_shap_global_bar.png"), bbox_inches="tight")
plt.close()
print(f"  Saved -> plots/08_shap_global_bar.png")

# Plot B — Beeswarm (direction + magnitude per feature across all deals)
# LEARNING NOTE:
#   Each dot = one deal. X-axis = SHAP value (positive = pushes toward Won).
#   Colour = the actual feature value for that deal (red = high, blue = low).
#   How to read it:
#     - agent_trailing_12m_win_rate: dots on the RIGHT are RED
#       -> high win rate agents tend to win more (makes sense)
#     - days_in_negotiation_stage: dots on the LEFT are RED
#       -> long negotiations push DOWN the win probability (matches business rule)
plt.figure(figsize=(10, 8))
shap.plots.beeswarm(explanation_1d, max_display=20, show=False)
plt.title("SHAP Beeswarm: Feature Impact Direction (test set)", fontsize=12, pad=12)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "09_shap_beeswarm.png"), bbox_inches="tight")
plt.close()
print(f"  Saved -> plots/09_shap_beeswarm.png")

# Plot C & D — Waterfall for one Won deal and one Lost deal
# LEARNING NOTE:
#   A waterfall chart shows the full breakdown for a SINGLE deal.
#   It starts at the base value (0.73) and each feature adds or subtracts.
#   Reading left to right: each bar is one feature's contribution.
#   Red bars = pushed toward Won, Blue bars = pushed toward Lost.
#   The final bar = the model's predicted probability for this exact deal.
#   This is what we will show in the Power BI "Individual Deal Intelligence" page.

proba = model.predict_proba(X_test)[:, 1]

# Pick an interesting Won example: real Win with probability around 0.85 (not trivially certain)
won_mask  = (y_test == 1).values
won_proba = proba[won_mask]
won_idx_within_won = np.argmin(np.abs(won_proba - 0.85))
won_idx = np.where(won_mask)[0][won_idx_within_won]

# Pick an interesting Lost example: real Loss with probability around 0.3 (model is uncertain)
lost_mask  = (y_test == 0).values
lost_proba = proba[lost_mask]
lost_idx_within_lost = np.argmin(np.abs(lost_proba - 0.35))
lost_idx = np.where(lost_mask)[0][lost_idx_within_lost]

for label, idx, fname in [
    ("Won", won_idx, "10_shap_waterfall_won_example.png"),
    ("Lost", lost_idx, "11_shap_waterfall_lost_example.png"),
]:
    plt.figure(figsize=(10, 7))
    shap.plots.waterfall(explanation_1d[idx], max_display=15, show=False)
    opp_id   = df["opportunity_id"].iloc[idx]
    pred_p   = proba[idx]
    actual   = "Won" if y_test.iloc[idx] == 1 else "Lost"
    plt.title(
        f"Deal breakdown: {opp_id}  |  Actual={actual}  |  Predicted={pred_p:.2f}",
        fontsize=11, pad=12,
    )
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, fname), bbox_inches="tight")
    plt.close()
    print(f"  Saved -> plots/{fname}  (deal {opp_id}, actual={actual}, prob={pred_p:.2f})")


# ── 6. top_shap_factors() — the helper 05_score.py will import ───────────────
# This function will be called for every open deal during scoring.
# It returns the top 3 reasons the model thinks a deal will Win or Lose.
# These strings go into the ML_PREDICTIONS table and appear in Power BI.

def top_shap_factors(shap_row: np.ndarray, feature_names: list, n: int = 3):
    """
    Given SHAP values for a single deal, return the top n features
    pushing TOWARD Won (positive) and top n pushing TOWARD Lost (negative).

    Returns:
        positive_factors : comma-separated string, e.g. "agent_trailing_12m_win_rate, client_win_rate"
        negative_factors : comma-separated string, e.g. "days_in_negotiation_stage, discount_pct"
    """
    # Sort features by absolute SHAP value (biggest movers first)
    sorted_idx = np.argsort(np.abs(shap_row))[::-1]

    positive = [feature_names[i] for i in sorted_idx if shap_row[i] > 0][:n]
    negative = [feature_names[i] for i in sorted_idx if shap_row[i] < 0][:n]

    return ", ".join(positive), ", ".join(negative)


# Quick demo: print the top factors for the two example deals
print("\n  Example: top SHAP factors per deal")
print(f"  {'Deal':<15} {'Actual':<8} {'Prob':<8} {'Top positive (Win drivers)':<45} {'Top negative (Risk factors)'}")
print(f"  {'-'*15} {'-'*8} {'-'*8} {'-'*45} {'-'*30}")

for label, idx in [("Won ex.", won_idx), ("Lost ex.", lost_idx)]:
    opp_id  = df["opportunity_id"].iloc[idx]
    actual  = "Won" if y_test.iloc[idx] == 1 else "Lost"
    pred_p  = proba[idx]
    pos, neg = top_shap_factors(shap_vals[idx], feat_cols, n=3)
    print(f"  {opp_id:<15} {actual:<8} {pred_p:<8.2f} {pos:<45} {neg}")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SHAP COMPLETE")
print("=" * 60)
print(f"  Base value (model prior)    : {base_val:.4f}")
print(f"  #1 global driver            : {mean_abs_shap.index[0]}  ({mean_abs_shap.iloc[0]:.5f})")
print(f"  #2 global driver            : {mean_abs_shap.index[1]}  ({mean_abs_shap.iloc[1]:.5f})")
print(f"  #3 global driver            : {mean_abs_shap.index[2]}  ({mean_abs_shap.iloc[2]:.5f})")
print()
print("  Plots saved (open them to understand what the model learned):")
print("    08 -- global bar   : which features matter most overall")
print("    09 -- beeswarm     : direction of each feature's effect")
print("    10 -- waterfall Won  : full breakdown for one Won deal")
print("    11 -- waterfall Lost : full breakdown for one Lost deal")
print()
print("  NEXT STEP: run ml/05_score.py  (predict on all open deals)")
print("=" * 60)
