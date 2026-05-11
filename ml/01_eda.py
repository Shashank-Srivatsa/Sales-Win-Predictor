"""
01_eda.py — Exploratory Data Analysis

PURPOSE:
  Before you train any model, you need to understand the data.
  EDA answers four critical questions:
    1. Class balance    — how lopsided is Won vs Lost? (drives EVERYTHING downstream)
    2. Feature signal   — do our features actually differ between Won and Lost?
    3. Data quality     — are there NULLs or outliers that will silently hurt the model?
    4. Business sanity  — do the patterns match what the business told us?

HOW TO RUN:
  cd Sales-Win-Predictor
  export SNOWFLAKE_ACCOUNT=... (or use .env)
  python ml/01_eda.py

OUTPUT:
  ml/plots/01_class_balance.png
  ml/plots/02_feature_distributions.png
  ml/plots/03_missing_values.png
  ml/plots/04_correlation_matrix.png
  ml/plots/05_division_analysis.png
  Console: printed summary statistics
"""

import os
import warnings
import snowflake.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

warnings.filterwarnings('ignore')

# config.py lives in the same ml/ folder
import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import SNOWFLAKE_CONFIG, FEATURE_COLS, TARGET_COL, ID_COL, PLOTS_DIR

# ── 0. Setup ─────────────────────────────────────────────────────────────────
os.makedirs(PLOTS_DIR, exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 130

print("=" * 60)
print("  SALES WIN PREDICTOR — EDA")
print("=" * 60)

# ── 1. Load data from Snowflake ───────────────────────────────────────────────
# We load ALL rows (train + test + score) so we can see the full dataset.
# During training we'll filter to ml_split IN ('train','test').
print("\n[1/5] Connecting to Snowflake and loading ml_deal_features...")

conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df = pd.read_sql(
    """
    SELECT *
    FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
    ORDER BY FISCAL_YEAR, OPPORTUNITY_ID
    """,
    conn
)
conn.close()

# Snowflake returns column names in UPPERCASE — normalise to lowercase for ease
df.columns = df.columns.str.lower()

print(f"  Loaded {len(df):,} rows × {len(df.columns)} columns")
print(f"  ml_split breakdown:\n{df['ml_split'].value_counts().to_string()}")


# ── 2. Class Balance ──────────────────────────────────────────────────────────
# LEARNING NOTE:
#   "Class imbalance" means one outcome (Lost) is much more common than the other (Won).
#   If 70% of deals are lost and we train naively, the model can reach 70% accuracy
#   by just predicting "Lost" every time — useless! That's why accuracy is a bad metric
#   here, and why we'll use ROC-AUC and F1 instead.
#   We also handle imbalance in training with scale_pos_weight (explained in 02_train.py).
print("\n[2/5] Analysing class balance...")

closed = df[df[TARGET_COL].notna()].copy()
closed[TARGET_COL] = closed[TARGET_COL].astype(int)
open_deals = df[df[TARGET_COL].isna()]

won_count  = (closed[TARGET_COL] == 1).sum()
lost_count = (closed[TARGET_COL] == 0).sum()
total_closed = len(closed)

print(f"  Closed deals : {total_closed:,}")
print(f"    Won        : {won_count:,}  ({won_count/total_closed*100:.1f}%)")
print(f"    Lost       : {lost_count:,}  ({lost_count/total_closed*100:.1f}%)")
print(f"  Open deals   : {len(open_deals):,}  (these are our SCORING targets)")
print(f"  scale_pos_weight to use in XGBoost: {lost_count/won_count:.2f}")
print("  -> Imbalance ratio tells XGBoost to weight the minority class more during training")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Class Balance — Closed Deals Only", fontsize=14, fontweight="bold")

# Pie chart
axes[0].pie(
    [won_count, lost_count],
    labels=["Won", "Lost"],
    colors=["#2ecc71", "#e74c3c"],
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 13}
)
axes[0].set_title("Won vs Lost (closed deals)")

# Bar chart by fiscal year
yearly = (
    closed.groupby(["fiscal_year", TARGET_COL])
    .size()
    .unstack(fill_value=0)
    .rename(columns={0: "Lost", 1: "Won"})
)
yearly.plot(kind="bar", ax=axes[1], color=["#e74c3c", "#2ecc71"], edgecolor="white", width=0.7)
axes[1].set_title("Won vs Lost by Fiscal Year")
axes[1].set_xlabel("Fiscal Year")
axes[1].set_ylabel("Deal Count")
axes[1].tick_params(axis="x", rotation=0)
axes[1].legend(loc="upper left")

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "01_class_balance.png"))
plt.close()
print(f"  Saved -> plots/01_class_balance.png")


# ── 3. Feature Signal ─────────────────────────────────────────────────────────
# LEARNING NOTE:
#   "Signal" means the feature value differs meaningfully between Won and Lost deals.
#   We visualise this with boxplots — if the Won box and Lost box barely overlap,
#   that feature is probably powerful. If they're identical, the feature adds nothing.
#   This is a quick sanity check: features that show NO signal here are suspicious.
print("\n[3/5] Analysing feature signal (Won vs Lost distributions)...")

# Pick the most interpretable features for the plot (not all 33 — too crowded)
KEY_FEATURES = [
    "deal_value_log",
    "discount_pct",
    "total_days_in_funnel",
    "days_in_negotiation_stage",
    "agent_trailing_12m_win_rate",
    "client_win_rate",
    "engagement_score",
    "days_since_last_activity",
    "stage_regression_count",
    "deal_velocity_score",
    "line_item_count",
    "contract_revision_count",
]

# Keep only features that actually exist in the loaded dataframe
key_feats_available = [f for f in KEY_FEATURES if f in closed.columns]

n_feats = len(key_feats_available)
n_cols  = 3
n_rows  = (n_feats + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 3.5))
fig.suptitle("Feature Distributions: Won vs Lost", fontsize=14, fontweight="bold", y=1.01)
axes = axes.flatten()

for i, feat in enumerate(key_feats_available):
    data_won  = closed.loc[closed[TARGET_COL] == 1, feat].dropna()
    data_lost = closed.loc[closed[TARGET_COL] == 0, feat].dropna()

    axes[i].boxplot(
        [data_won, data_lost],
        labels=["Won", "Lost"],
        patch_artist=True,
        boxprops=dict(facecolor="#2ecc7180"),
        medianprops=dict(color="black", linewidth=2),
    )
    # Colour the Lost box differently
    axes[i].findobj(plt.matplotlib.patches.PathPatch)[1].set_facecolor("#e74c3c80")

    axes[i].set_title(feat, fontsize=10)
    axes[i].set_ylabel("Value")

    # Print the median difference as a quick signal score
    sep = abs(data_won.median() - data_lost.median())
    axes[i].set_xlabel(f"median gap = {sep:.2f}", fontsize=8, color="grey")

for j in range(i + 1, len(axes)):
    axes[j].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "02_feature_distributions.png"), bbox_inches="tight")
plt.close()
print(f"  Saved -> plots/02_feature_distributions.png")
print("  TIP: features with large median gaps (Won box vs Lost box) will matter most in SHAP")


# ── 4. Missing Value Report ───────────────────────────────────────────────────
# LEARNING NOTE:
#   XGBoost handles NULLs natively — it learns which direction to go when a value
#   is missing. But we still need to know WHERE NULLs are and WHY, because:
#   - A NULL in 'days_since_last_activity' means "no activity ever" — that's informative!
#   - A NULL in 'client_win_rate' means "new client" — also informative.
#   - Our feature table already COALESCEs most NULLs to defaults, but let's verify.
print("\n[4/5] Checking data quality (missing values)...")

all_cols = FEATURE_COLS + [TARGET_COL, ID_COL, "ml_split", "fiscal_year"]
available_cols = [c for c in all_cols if c in df.columns]

null_report = (
    df[available_cols]
    .isnull()
    .sum()
    .reset_index()
    .rename(columns={"index": "column", 0: "null_count"})
)
null_report["null_pct"] = (null_report["null_count"] / len(df) * 100).round(2)
null_report = null_report[null_report["null_count"] > 0].sort_values("null_pct", ascending=False)

if null_report.empty:
    print("  No missing values in feature columns — COALESCE defaults working correctly")
else:
    print("  Columns with missing values:")
    print(null_report.to_string(index=False))
    print("  NOTE: NULL in target_is_won is expected — those are open/scoring deals")

fig, ax = plt.subplots(figsize=(10, max(4, len(null_report) * 0.5 + 1)))

if null_report.empty:
    ax.text(0.5, 0.5, "No missing values\nin feature columns", ha="center", va="center",
            fontsize=16, color="green", transform=ax.transAxes)
    ax.set_axis_off()
else:
    bars = ax.barh(null_report["column"], null_report["null_pct"], color="#3498db")
    ax.set_xlabel("% Missing")
    ax.set_title("Missing Value Report (% of all rows)")
    for bar, pct in zip(bars, null_report["null_pct"]):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "03_missing_values.png"))
plt.close()
print(f"  Saved -> plots/03_missing_values.png")


# ── 5. Correlation Matrix ─────────────────────────────────────────────────────
# LEARNING NOTE:
#   High correlation between two features = they're telling the model the same thing.
#   This is called "multicollinearity". For XGBoost it's mostly harmless (the model
#   will just split on whichever is slightly stronger), but it:
#   - Wastes computation
#   - Makes SHAP values harder to interpret (credit gets split between correlated features)
#   Anything above 0.85 is worth investigating.
print("\n[5/5] Computing feature correlation matrix...")

feat_cols_available = [f for f in FEATURE_COLS if f in closed.columns]
corr = closed[feat_cols_available].corr()

fig, ax = plt.subplots(figsize=(18, 15))
mask = np.triu(np.ones_like(corr, dtype=bool))   # only show lower triangle
sns.heatmap(
    corr,
    mask=mask,
    ax=ax,
    cmap="RdYlGn",
    vmin=-1, vmax=1,
    center=0,
    linewidths=0.4,
    annot=False,          # too many cells for numbers — just use colour
    square=True,
    cbar_kws={"shrink": 0.6},
)
ax.set_title("Feature Correlation Matrix (closed deals only)", fontsize=13, fontweight="bold")
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "04_correlation_matrix.png"))
plt.close()

# Flag high correlations for the user
high_corr_pairs = []
for i in range(len(corr.columns)):
    for j in range(i + 1, len(corr.columns)):
        val = corr.iloc[i, j]
        if abs(val) > 0.75:
            high_corr_pairs.append((corr.columns[i], corr.columns[j], round(val, 3)))

if high_corr_pairs:
    print("  High correlations (|r| > 0.75) — these features overlap:")
    for a, b, r in sorted(high_corr_pairs, key=lambda x: -abs(x[2])):
        print(f"    {a}  <->  {b}  :  r = {r}")
else:
    print("  No strongly correlated feature pairs — good feature diversity")
print(f"  Saved -> plots/04_correlation_matrix.png")


# ── 6. Business Sanity Check — Win Rate by Division ──────────────────────────
# LEARNING NOTE:
#   Always verify the data matches what the domain experts told you.
#   The spec says: "BrandVault deals are hardest to close; PulseMedia closes most reliably"
#   If the data contradicts this, either the data is wrong or the assumption is wrong.
#   Either way, you want to know BEFORE training.
print("\n[+] Business sanity check — win rate by division & region...")

div_stats = (
    closed
    .groupby("division_encoded")[TARGET_COL]
    .agg(["mean", "count"])
    .rename(columns={"mean": "win_rate", "count": "deals"})
    .reset_index()
)
div_label_map = {0: "TalentEdge", 1: "CreativeMotion", 2: "PulseMedia", 3: "BrandVault"}
div_stats["division"] = div_stats["division_encoded"].map(div_label_map)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Business Sanity Checks", fontsize=13, fontweight="bold")

div_stats_sorted = div_stats.sort_values("win_rate", ascending=True)
bars = axes[0].barh(div_stats_sorted["division"], div_stats_sorted["win_rate"],
                    color="#3498db", edgecolor="white")
axes[0].set_xlabel("Win Rate")
axes[0].set_title("Win Rate by Division\n(expect: PulseMedia high, BrandVault low)")
axes[0].set_xlim(0, 1)
for bar, (_, row) in zip(bars, div_stats_sorted.iterrows()):
    axes[0].text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{row['win_rate']:.1%}  (n={int(row['deals'])})",
                 va="center", fontsize=9)

# Win rate by agent seniority
if "agent_seniority_level" in closed.columns:
    sen_stats = (
        closed.groupby("agent_seniority_level")[TARGET_COL]
        .agg(["mean", "count"])
        .rename(columns={"mean": "win_rate", "count": "deals"})
        .reset_index()
    )
    sen_label_map = {1: "Junior", 2: "Mid", 3: "Senior", 4: "Director", 5: "VP/Head"}
    sen_stats["label"] = sen_stats["agent_seniority_level"].map(sen_label_map)

    axes[1].bar(sen_stats["label"], sen_stats["win_rate"],
                color="#9b59b6", edgecolor="white")
    axes[1].set_title("Win Rate by Agent Seniority\n(expect: higher seniority = higher win rate)")
    axes[1].set_ylabel("Win Rate")
    axes[1].set_ylim(0, 1)
    for i, row in sen_stats.iterrows():
        axes[1].text(i, row["win_rate"] + 0.01, f"{row['win_rate']:.1%}", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "05_business_sanity.png"))
plt.close()
print(f"  Saved -> plots/05_business_sanity.png")


# ── 7. Summary printout ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  EDA COMPLETE — Summary")
print("=" * 60)
print(f"  Total rows loaded       : {len(df):,}")
print(f"  Training rows (closed)  : {total_closed:,}")
print(f"  Scoring rows (open)     : {len(open_deals):,}")
print(f"  Won / Lost ratio        : {won_count:,} / {lost_count:,}")
print(f"  Imbalance (scale_pos_w) : {lost_count/won_count:.2f}x")
print(f"  Features available      : {len(feat_cols_available)} / {len(FEATURE_COLS)}")
print(f"  Plots saved to          : {PLOTS_DIR}")
print()
print("  NEXT STEP: run ml/02_train.py")
print("=" * 60)
