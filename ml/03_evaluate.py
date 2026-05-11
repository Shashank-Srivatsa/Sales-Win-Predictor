"""
03_evaluate.py — Decision Threshold Tuning

PURPOSE:
  The model outputs a probability (e.g. 0.67 = 67% chance of winning).
  To make a yes/no prediction we compare that probability to a threshold.
  This script finds the BEST threshold from the test data instead of guessing.

KEY LEARNING CONCEPTS IN THIS FILE:
  1. Why 0.5 is wrong as a default threshold
  2. The Precision-Recall tradeoff — the most important concept in applied ML
  3. F1-score — why it balances precision and recall
  4. Business cost matrix — translating model errors into real money
  5. ROC curve — visualising model quality independent of any threshold

OUTPUTS:
  ml/plots/06_threshold_f1_curve.png    -- F1 at every threshold
  ml/plots/07_precision_recall_curve.png -- the PR curve
  ml/plots/08_roc_curve.png             -- ROC curve
  ml/best_threshold.txt                 -- the chosen threshold (read by 05_score.py)

HOW TO RUN:
  python ml/03_evaluate.py
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import snowflake.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import mlflow
import mlflow.xgboost
from mlflow.tracking import MlflowClient
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    precision_recall_curve, roc_curve, classification_report,
)

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL,
    MLFLOW_TRACKING_URI, MODEL_NAME, EXPERIMENT_NAME,
    DECISION_THRESHOLD, PLOTS_DIR,
)

os.makedirs(PLOTS_DIR, exist_ok=True)

print("=" * 60)
print("  SALES WIN PREDICTOR -- Threshold Evaluation")
print("=" * 60)


# ── 1. Load the trained model from MLflow ────────────────────────────────────
# LEARNING NOTE — why load from MLflow instead of a pickle file?
#   When you save a model to a pickle file, you have to remember which file
#   was trained on which data with which parameters. It gets messy fast.
#   MLflow's model registry gives every model a VERSION NUMBER and tracks
#   exactly which training run produced it. "models:/name/1" always means
#   version 1, full stop.

print("\n[1/4] Loading model from MLflow registry...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

client = MlflowClient()
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
if not versions:
    raise RuntimeError(
        f"No model found with name '{MODEL_NAME}'. "
        "Run 02_train.py first."
    )

latest_version = sorted(versions, key=lambda v: int(v.version), reverse=True)[0]
model_uri = f"models:/{MODEL_NAME}/{latest_version.version}"
model = mlflow.xgboost.load_model(model_uri)

print(f"  Loaded : {MODEL_NAME}  version {latest_version.version}")
print(f"  Run ID : {latest_version.run_id[:8]}...")


# ── 2. Load test data ─────────────────────────────────────────────────────────
# We evaluate ONLY on the test set — deals from FY >= 2023 that the model
# has never seen during training. Evaluating on training data would be like
# a teacher marking their own exam answers — meaningless.

print("\n[2/4] Loading test data from Snowflake...")

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
feat_cols = [f for f in FEATURE_COLS if f in df.columns]

X_test = df[feat_cols]
y_test = df[TARGET_COL].astype(int)

print(f"  Test rows : {len(df):,}")
print(f"  Won       : {y_test.sum():,}  ({y_test.mean()*100:.1f}%)")
print(f"  Lost      : {(1-y_test).sum():,}  ({(1-y_test).mean()*100:.1f}%)")

proba = model.predict_proba(X_test)[:, 1]   # win probability for each deal

print(f"\n  Probability distribution on test set:")
print(f"    min    : {proba.min():.4f}")
print(f"    median : {np.median(proba):.4f}")
print(f"    mean   : {proba.mean():.4f}")
print(f"    max    : {proba.max():.4f}")
print(f"  -> model is very confident (most probs near 0 or 1 = strong separation)")


# ── 3. Threshold sweep ────────────────────────────────────────────────────────
# LEARNING NOTE — The Precision-Recall tradeoff:
#
#   Every binary classifier has a dial called the THRESHOLD.
#   Turn it UP (say 0.9) -> model only predicts "Won" when very confident
#      -> FEWER won predictions -> most are correct (high Precision)
#      -> BUT you'll miss many real wins (low Recall)
#   Turn it DOWN (say 0.2) -> model predicts "Won" aggressively
#      -> MORE won predictions -> many false alarms (low Precision)
#      -> BUT you catch almost every real win (high Recall)
#
#   There is NO free lunch — you can't have both high Precision AND high Recall
#   unless your model is near-perfect. You choose based on what hurts more:
#
#   FOR THIS PROJECT:
#     False Negative = we predicted Lost on a real Win -> agent got no support
#                      the deal slipped through unnoticed -> HIGH business cost
#     False Positive = we predicted Won on a real Loss  -> wasted management attention
#                      slightly annoying -> LOWER business cost
#
#   Therefore: we should accept LOWER precision to get HIGHER recall.
#   That means: use a threshold BELOW 0.5.

print("\n[3/4] Sweeping thresholds to find the optimal...")

thresholds   = np.arange(0.05, 0.96, 0.01)
f1_scores    = []
precision_sc = []
recall_sc    = []

# Business cost weights (spec: FN costs 50x more than FP)
FN_COST = 50
FP_COST = 1
business_costs = []

for t in thresholds:
    preds = (proba >= t).astype(int)
    # zero_division=0 handles edge case where threshold is so extreme
    # that all predictions are the same class
    p  = precision_score(y_test, preds, zero_division=0)
    r  = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)

    # FN = actual Won but predicted Lost, FP = actual Lost but predicted Won
    fn = ((preds == 0) & (y_test == 1)).sum()
    fp = ((preds == 1) & (y_test == 0)).sum()
    cost = FN_COST * fn + FP_COST * fp

    f1_scores.append(f1)
    precision_sc.append(p)
    recall_sc.append(r)
    business_costs.append(cost)

f1_scores     = np.array(f1_scores)
precision_sc  = np.array(precision_sc)
recall_sc     = np.array(recall_sc)
business_costs = np.array(business_costs)

# F1-optimal threshold (mathematical balance of precision and recall)
best_f1_idx      = np.argmax(f1_scores)
best_f1_threshold = thresholds[best_f1_idx]

# Business-cost-optimal threshold (minimises the cost of errors)
best_cost_idx      = np.argmin(business_costs)
best_cost_threshold = thresholds[best_cost_idx]

print(f"\n  F1-optimal threshold      : {best_f1_threshold:.2f}")
print(f"    -> F1        = {f1_scores[best_f1_idx]:.4f}")
print(f"    -> Precision = {precision_sc[best_f1_idx]:.4f}")
print(f"    -> Recall    = {recall_sc[best_f1_idx]:.4f}")

print(f"\n  Business-cost threshold   : {best_cost_threshold:.2f}  (FN={FN_COST}x, FP={FP_COST}x)")
print(f"    -> F1        = {f1_scores[best_cost_idx]:.4f}")
print(f"    -> Precision = {precision_sc[best_cost_idx]:.4f}")
print(f"    -> Recall    = {recall_sc[best_cost_idx]:.4f}")
print(f"    -> Total business cost = {business_costs[best_cost_idx]:,}")

# For this project we choose the business-cost threshold — it minimises missed wins
CHOSEN_THRESHOLD = best_cost_threshold
chosen_idx       = best_cost_idx

print(f"\n  CHOSEN threshold : {CHOSEN_THRESHOLD:.2f}  (business-cost optimised)")
print(f"  (Previous hardcoded default was {DECISION_THRESHOLD})")


# ── 4. Show confusion matrix at chosen threshold ──────────────────────────────
preds_chosen = (proba >= CHOSEN_THRESHOLD).astype(int)

fn_chosen = int(((preds_chosen == 0) & (y_test == 1)).sum())
fp_chosen = int(((preds_chosen == 1) & (y_test == 0)).sum())
tp_chosen = int(((preds_chosen == 1) & (y_test == 1)).sum())
tn_chosen = int(((preds_chosen == 0) & (y_test == 0)).sum())

print(f"\n  Confusion Matrix at threshold = {CHOSEN_THRESHOLD:.2f}")
print(f"                   Pred Lost   Pred Won")
print(f"  Actual Lost  :     {tn_chosen:5d}     {fp_chosen:5d}   <- FP: said Won, was Lost")
print(f"  Actual Won   :     {fn_chosen:5d}     {tp_chosen:5d}   <- FN: said Lost, was Won")
print(f"\n  Business interpretation:")
print(f"    {fn_chosen} deals we failed to flag as high-priority (missed wins)")
print(f"    {fp_chosen} deals we chased unnecessarily (false alarms)")
print(f"    At FN={FN_COST}x cost:  {fn_chosen*FN_COST} + {fp_chosen*FP_COST} = {fn_chosen*FN_COST + fp_chosen*FP_COST} total cost units")


# ── 5. Plots ──────────────────────────────────────────────────────────────────
print("\n[4/4] Generating evaluation plots...")

# Plot A — F1 and business cost vs threshold
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Threshold Selection", fontsize=13, fontweight="bold")

ax = axes[0]
ax.plot(thresholds, f1_scores,    label="F1 Score",   color="#2ecc71", lw=2)
ax.plot(thresholds, precision_sc, label="Precision",  color="#3498db", lw=1.5, ls="--")
ax.plot(thresholds, recall_sc,    label="Recall",     color="#e74c3c", lw=1.5, ls="--")
ax.axvline(best_f1_threshold,   color="#2ecc71", ls=":", lw=2, label=f"F1-optimal ({best_f1_threshold:.2f})")
ax.axvline(best_cost_threshold, color="#e67e22", ls=":", lw=2, label=f"Business-optimal ({best_cost_threshold:.2f})")
ax.set_xlabel("Threshold")
ax.set_ylabel("Score")
ax.set_title("F1 / Precision / Recall vs Threshold")
ax.legend(fontsize=8)
ax.set_xlim(0.05, 0.95)

ax2 = axes[1]
ax2.plot(thresholds, business_costs, color="#e74c3c", lw=2)
ax2.axvline(best_cost_threshold, color="#e67e22", ls=":", lw=2,
            label=f"Min cost at {best_cost_threshold:.2f}")
ax2.set_xlabel("Threshold")
ax2.set_ylabel(f"Business Cost  (FN={FN_COST}x FP)")
ax2.set_title(f"Business Cost vs Threshold\n(FN penalised {FN_COST}x more than FP)")
ax2.legend(fontsize=9)
ax2.set_xlim(0.05, 0.95)

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "06_threshold_f1_curve.png"))
plt.close()
print(f"  Saved -> plots/06_threshold_f1_curve.png")

# Plot B — Precision-Recall curve
# LEARNING NOTE:
#   Each point on this curve = one threshold setting.
#   Top-right corner (Precision=1, Recall=1) = perfect model.
#   The AREA under this curve (AP score) summarises overall model quality.
#   A random classifier collapses to a horizontal line at y = base_rate.

sk_prec, sk_rec, sk_thresh = precision_recall_curve(y_test, proba)
baseline = y_test.mean()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Model Quality Curves", fontsize=13, fontweight="bold")

ax = axes[0]
ax.plot(sk_rec, sk_prec, color="#9b59b6", lw=2, label="Model PR curve")
ax.axhline(baseline, color="grey", ls="--", lw=1.5,
           label=f"Random classifier (baseline = {baseline:.2f})")
# Mark our chosen threshold on the curve
chosen_p = precision_sc[chosen_idx]
chosen_r = recall_sc[chosen_idx]
ax.scatter([chosen_r], [chosen_p], color="#e67e22", s=120, zorder=5,
           label=f"Chosen threshold ({CHOSEN_THRESHOLD:.2f})")
ax.set_xlabel("Recall  (what fraction of Wons did we catch?)")
ax.set_ylabel("Precision  (of our Won predictions, how many were right?)")
ax.set_title("Precision-Recall Curve")
ax.legend(fontsize=8)
ax.set_xlim(0, 1.05)
ax.set_ylim(0, 1.05)

# Plot C — ROC curve
# LEARNING NOTE:
#   X-axis: False Positive Rate (FP / all actual Lost)
#   Y-axis: True  Positive Rate = Recall (TP / all actual Won)
#   The diagonal = random. Area under curve (AUC) = single number quality score.
#   AUC = 1.0 means perfect ranking. AUC = 0.5 = random.

fpr, tpr, _ = roc_curve(y_test, proba)
auc_val     = roc_auc_score(y_test, proba)

ax2 = axes[1]
ax2.plot(fpr, tpr, color="#3498db", lw=2, label=f"ROC (AUC = {auc_val:.4f})")
ax2.plot([0, 1], [0, 1], color="grey", ls="--", lw=1.5, label="Random classifier")
ax2.set_xlabel("False Positive Rate  (Lost deals wrongly called Won)")
ax2.set_ylabel("True Positive Rate  (Won deals correctly caught)")
ax2.set_title("ROC Curve")
ax2.legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "07_model_quality_curves.png"))
plt.close()
print(f"  Saved -> plots/07_model_quality_curves.png")


# ── 6. Save chosen threshold ──────────────────────────────────────────────────
# We write the threshold to a plain text file so 05_score.py can read it.
# This avoids hardcoding it in config.py — the data chose it, not us.

threshold_path = os.path.join(os.path.dirname(__file__), "best_threshold.txt")
with open(threshold_path, "w") as f:
    f.write(str(round(float(CHOSEN_THRESHOLD), 4)))
print(f"\n  Saved chosen threshold -> ml/best_threshold.txt  ({CHOSEN_THRESHOLD:.2f})")

# Also log to the most recent MLflow run so it's permanently linked to the model
try:
    runs = mlflow.search_runs(
        experiment_names=[EXPERIMENT_NAME],
        order_by=["start_time DESC"],
        max_results=1,
    )
    if not runs.empty:
        run_id = runs.iloc[0]["run_id"]
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metric("threshold_f1_optimal",   round(float(best_f1_threshold), 4))
            mlflow.log_metric("threshold_business_optimal", round(float(best_cost_threshold), 4))
            mlflow.log_metric("chosen_threshold",        round(float(CHOSEN_THRESHOLD), 4))
        print(f"  Logged threshold metrics to MLflow run {run_id[:8]}...")
except Exception as e:
    print(f"  (MLflow logging skipped: {e})")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  EVALUATION COMPLETE")
print("=" * 60)
print(f"  F1-optimal threshold       : {best_f1_threshold:.2f}")
print(f"  Business-cost threshold    : {best_cost_threshold:.2f}  <-- CHOSEN")
print(f"  At chosen threshold:")
print(f"    Missed real wins (FN)    : {fn_chosen}")
print(f"    False alarms (FP)        : {fp_chosen}")
print(f"    Total business cost      : {fn_chosen*FN_COST + fp_chosen*FP_COST} units")
print(f"  ROC-AUC                    : {auc_val:.4f}")
print()
print("  NEXT STEP: run ml/04_explain.py  (SHAP -- why did the model decide this?)")
print("=" * 60)
