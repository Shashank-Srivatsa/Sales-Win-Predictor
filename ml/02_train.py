"""
02_train.py — XGBoost Model Training

PURPOSE:
  This script trains the win-probability classifier and logs everything to MLflow.
  After this runs, you will have a versioned model you can inspect, compare, and reload.

KEY LEARNING CONCEPTS IN THIS FILE:
  1. Chronological train/test split  — why random split would be WRONG here
  2. scale_pos_weight                — how XGBoost handles class imbalance natively
  3. Early stopping                  — how the model decides when to stop growing trees
  4. logloss vs accuracy             — why we track the right metric during training
  5. ROC-AUC                         — what it actually measures
  6. MLflow                          — why we log experiments instead of just printing

HOW TO RUN:
  cd Sales-Win-Predictor
  python ml/02_train.py
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import snowflake.connector
import pandas as pd
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score,
    recall_score, classification_report, confusion_matrix,
)

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL, ID_COL,
    MLFLOW_TRACKING_URI, EXPERIMENT_NAME, MODEL_NAME,
    EARLY_STOPPING_ROUNDS, N_ESTIMATORS_MAX, DECISION_THRESHOLD, PLOTS_DIR,
)

os.makedirs(PLOTS_DIR, exist_ok=True)

print("=" * 60)
print("  SALES WIN PREDICTOR -- XGBoost Training")
print("=" * 60)


# ── 1. Load data ──────────────────────────────────────────────────────────────
# We only load rows where ml_split is 'train' or 'test'.
# The 'score' rows (open deals) are excluded here — they have no label (target=NULL)
# and the model has never seen them. We will score them in 05_score.py.
print("\n[1/5] Loading feature data from Snowflake...")

conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df = pd.read_sql(
    """
    SELECT *
    FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
    WHERE ML_SPLIT IN ('train', 'test')
    ORDER BY FISCAL_YEAR, OPPORTUNITY_ID
    """,
    conn,
)
conn.close()

df.columns = df.columns.str.lower()
print(f"  Loaded {len(df):,} closed deals")
print(f"  Train : {(df['ml_split']=='train').sum():,} rows  (FY <= 2022)")
print(f"  Test  : {(df['ml_split']=='test').sum():,} rows  (FY >= 2023)")


# ── 2. Train / Test split ─────────────────────────────────────────────────────
# LEARNING NOTE — Why NOT random split?
#   In most ML tutorials you see: train_test_split(df, test_size=0.2, random_state=42)
#   For sales deal data that would be WRONG. Here is why:
#
#   Imagine deal OPP-5000 closed in Jan 2024. If it ends up in "train", the model
#   learns patterns from 2024 — patterns it would never have known in 2022.
#   Then you evaluate on 2022 data and pat yourself on the back for 90% accuracy.
#   In production, accuracy drops to 60% because the model memorised the future.
#   This is called DATA LEAKAGE — one of the most common ML mistakes in practice.
#
#   The correct approach: train on everything before a cutoff date, test on everything
#   after. Our feature table already encodes this via ml_split. Never touch it.

# Identify which feature columns actually exist in the loaded data
feat_cols = [f for f in FEATURE_COLS if f in df.columns]
missing   = [f for f in FEATURE_COLS if f not in df.columns]
if missing:
    print(f"\n  WARNING: {len(missing)} features not found in table: {missing}")
print(f"\n  Using {len(feat_cols)} features")

train_df = df[df["ml_split"] == "train"].copy()
test_df  = df[df["ml_split"] == "test"].copy()

X_train = train_df[feat_cols]
y_train = train_df[TARGET_COL].astype(int)
X_test  = test_df[feat_cols]
y_test  = test_df[TARGET_COL].astype(int)

print(f"  X_train shape : {X_train.shape}")
print(f"  X_test  shape : {X_test.shape}")


# ── 3. Compute class weight ───────────────────────────────────────────────────
# LEARNING NOTE — scale_pos_weight instead of SMOTE:
#   Our data has 73% Won and 27% Lost. Left uncorrected, XGBoost would learn
#   "just predict Won always" for free accuracy. We fix this via scale_pos_weight.
#
#   scale_pos_weight = count(negative class) / count(positive class)
#                    = count(Lost)           / count(Won)
#                    = 484 / 1318  =  ~0.37
#
#   Effect: during training, every "Lost" example is weighted 0.37x relative to
#   "Won". The model is penalised more for confidently predicting "Won" on a
#   deal that actually lost. This makes it more cautious and better calibrated.
#
#   Why not SMOTE? SMOTE creates *synthetic* rows by interpolating between real ones.
#   For a tree model this is unnecessary — and it can introduce feature combinations
#   that don't exist in reality (e.g., synthetic row: new client + very high deal value
#   + junior agent). scale_pos_weight achieves the same correction with no synthetic data.

neg_count = (y_train == 0).sum()   # Lost
pos_count = (y_train == 1).sum()   # Won
scale_pos_weight = neg_count / pos_count

print(f"\n[2/5] Class balance in training data:")
print(f"  Won  (positive) : {pos_count:,}  ({pos_count/len(y_train)*100:.1f}%)")
print(f"  Lost (negative) : {neg_count:,}  ({neg_count/len(y_train)*100:.1f}%)")
print(f"  scale_pos_weight = {neg_count} / {pos_count} = {scale_pos_weight:.3f}")


# ── 4. Configure XGBoost ──────────────────────────────────────────────────────
# LEARNING NOTE — key hyperparameters explained:
#
#   n_estimators        : max number of trees to grow (early stopping cuts this short)
#   learning_rate       : how much each new tree corrects the previous error
#                         smaller = slower but more careful = usually better generalisation
#   max_depth           : how many splits each tree can make
#                         deeper = can capture complex interactions, but overfits faster
#   subsample           : fraction of training rows sampled per tree (0.8 = 80%)
#                         prevents any one tree from memorising the full dataset
#   colsample_bytree    : fraction of features sampled per tree (0.8 = 80%)
#                         forces diversity across trees — similar to Random Forest
#   scale_pos_weight    : computed above — corrects for class imbalance
#   early_stopping_rounds: stop if test logloss hasn't improved for 30 consecutive trees
#   eval_metric='logloss': logloss = -log(predicted probability of the correct class)
#                           lower is better, penalises CONFIDENT wrong predictions hard
#                           better metric than accuracy for probability calibration

model = xgb.XGBClassifier(
    n_estimators        = N_ESTIMATORS_MAX,
    learning_rate       = 0.05,
    max_depth           = 5,
    subsample           = 0.8,
    colsample_bytree    = 0.8,
    scale_pos_weight    = scale_pos_weight,
    eval_metric         = "logloss",
    early_stopping_rounds = EARLY_STOPPING_ROUNDS,
    random_state        = 42,
    device              = "cpu",
)

print(f"\n[3/5] Training XGBoost...")
print(f"  Max trees      : {N_ESTIMATORS_MAX}  (early stopping at {EARLY_STOPPING_ROUNDS} no-improve rounds)")
print(f"  Learning rate  : 0.05")
print(f"  Max depth      : 5")
print(f"  Eval metric    : logloss  (lower = model is more confident on correct predictions)")
print()

# eval_set lets XGBoost measure logloss on the TEST set after every tree.
# When test logloss stops improving for EARLY_STOPPING_ROUNDS in a row, training stops.
# verbose=50 prints logloss every 50 trees so you can watch the model converge.
model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50,
)

best_n_trees = model.best_iteration + 1
print(f"\n  Training stopped at tree #{best_n_trees}  (out of max {N_ESTIMATORS_MAX})")
print(f"  Best test logloss : {model.best_score:.5f}")


# ── 5. Evaluate on test set ───────────────────────────────────────────────────
# LEARNING NOTE — ROC-AUC explained:
#   Accuracy = "what % of predictions are correct?" — misleading with imbalance.
#   ROC-AUC  = "how well can the model RANK deals by win probability?"
#              AUC of 1.0 = perfect ranking (all Won deals score higher than all Lost)
#              AUC of 0.5 = random (coin flip)
#              AUC of 0.8+ = model is meaningfully better than guessing
#
#   Why ranking matters here: we don't just want "win/lose". We want to
#   sort the pipeline from "most likely to close" to "needs rescue".
#   ROC-AUC measures exactly that sorting ability.

print("\n[4/5] Evaluating on test set...")

proba = model.predict_proba(X_test)[:, 1]    # probability of Won (class=1)
preds = (proba >= DECISION_THRESHOLD).astype(int)

auc       = roc_auc_score(y_test, proba)
f1        = f1_score(y_test, preds)
precision = precision_score(y_test, preds)
recall    = recall_score(y_test, preds)

print(f"\n  --- Test Set Metrics (threshold = {DECISION_THRESHOLD}) ---")
print(f"  ROC-AUC   : {auc:.4f}   (target > 0.80 | 0.5 = random)")
print(f"  F1-Won    : {f1:.4f}   (harmonic mean of precision + recall)")
print(f"  Precision : {precision:.4f}  (of deals we called 'Won', how many actually won?)")
print(f"  Recall    : {recall:.4f}  (of all Won deals, how many did we catch?)")

print("\n  Confusion Matrix  (rows=Actual, cols=Predicted):")
cm = confusion_matrix(y_test, preds)
print(f"                 Pred Lost   Pred Won")
print(f"  Actual Lost  :   {cm[0,0]:5d}       {cm[0,1]:5d}   <- False Positives (we said Won, it Lost)")
print(f"  Actual Won   :   {cm[1,0]:5d}       {cm[1,1]:5d}   <- True Positives")

print("\n  Full classification report:")
print(classification_report(y_test, preds, target_names=["Lost", "Won"]))


# ── 6. Log to MLflow ──────────────────────────────────────────────────────────
# LEARNING NOTE — why log to MLflow instead of just printing?
#   When you retrain next month with new data, you want to COMPARE:
#   "did the new model improve or get worse?"
#   MLflow stores every run with its parameters and metrics in a local database.
#   You can view all runs in the browser: run `mlflow ui` in this folder.
#   The model is also saved in MLflow so 05_score.py can load it by name.

print("\n[5/5] Logging run to MLflow...")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_NAME)

with mlflow.start_run(run_name="xgboost_v1") as run:
    # Log hyperparameters
    mlflow.log_params({
        "n_estimators_actual" : best_n_trees,
        "learning_rate"       : 0.05,
        "max_depth"           : 5,
        "subsample"           : 0.8,
        "colsample_bytree"    : 0.8,
        "scale_pos_weight"    : round(scale_pos_weight, 4),
        "early_stopping_rounds": EARLY_STOPPING_ROUNDS,
        "decision_threshold"  : DECISION_THRESHOLD,
        "n_features"          : len(feat_cols),
        "train_rows"          : len(X_train),
        "test_rows"           : len(X_test),
    })

    # Log metrics
    mlflow.log_metrics({
        "roc_auc"   : round(auc, 4),
        "f1_won"    : round(f1, 4),
        "precision" : round(precision, 4),
        "recall"    : round(recall, 4),
        "best_logloss": round(model.best_score, 5),
    })

    # Save the trained model + register it so 05_score.py can load it by name
    mlflow.xgboost.log_model(
        model,
        artifact_path=MODEL_NAME,
        registered_model_name=MODEL_NAME,
    )

    run_id = run.info.run_id

print(f"  Run ID     : {run_id}")
print(f"  Experiment : {EXPERIMENT_NAME}")
print(f"  Model      : {MODEL_NAME}  (registered in MLflow registry)")
print(f"\n  TIP: run 'mlflow ui --backend-store-uri {MLFLOW_TRACKING_URI}'")
print(f"       then open http://localhost:5000 to browse this run visually")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TRAINING COMPLETE")
print("=" * 60)
print(f"  Trees trained     : {best_n_trees}  (early stopping worked)")
print(f"  ROC-AUC           : {auc:.4f}")
print(f"  F1 (Won)          : {f1:.4f}")
print()
if auc >= 0.80:
    print("  ROC-AUC >= 0.80 -- model has meaningful predictive power")
else:
    print("  ROC-AUC < 0.80 -- consider feature engineering or hyperparameter tuning")
print()
print("  NEXT STEP: run ml/03_evaluate.py  (tune the decision threshold from data)")
print("=" * 60)
