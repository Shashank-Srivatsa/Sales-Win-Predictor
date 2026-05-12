"""
06_write_predictions.py — Write Predictions to Snowflake

PURPOSE:
  Take the scored predictions from 05_score.py and persist them to
  SALES_WIN_DB.ML.ML_PREDICTIONS in Snowflake.
  This table is the bridge between the ML pipeline and Power BI.

LEARNING NOTE — why append rather than overwrite?
  We run scoring every day. If we overwrote the table, we would lose the
  history of how a deal's probability changed over time.
  By appending, the table grows by 48 rows per day. The dbt model
  fact_opportunities_scored always picks the LATEST row per deal using
  ROW_NUMBER(), so Power BI always sees fresh predictions without losing history.

LEARNING NOTE — write_pandas vs INSERT statements:
  write_pandas() from snowflake-connector-python bulk-loads a DataFrame
  into Snowflake using a temporary stage (like COPY INTO). It is much
  faster than looping over rows and running individual INSERT statements.
  For 48 rows the difference is negligible, but for 50,000 rows it matters.

HOW TO RUN:
  python ml/06_write_predictions.py
  (runs 05_score.py automatically, then writes to Snowflake)
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import SNOWFLAKE_CONFIG

TARGET_TABLE    = "ML_PREDICTIONS"
TARGET_DATABASE = "SALES_WIN_DB"
TARGET_SCHEMA   = "ML"

print("=" * 60)
print("  SALES WIN PREDICTOR -- Writing Predictions to Snowflake")
print("=" * 60)


# ── 1. Run scoring (generates predictions_staging.csv) ───────────────────────
print("\n[1/3] Running 05_score.py to generate predictions...")
print("-" * 40)

# We run 05_score.py as a subprocess so its output is visible in full,
# then read the CSV it produces. This keeps each script independently runnable.
import subprocess, sys as _sys
result = subprocess.run(
    [_sys.executable, os.path.join(os.path.dirname(__file__), "05_score.py")],
    capture_output=False,   # let output stream to console so you can see it
)
if result.returncode != 0:
    raise RuntimeError("05_score.py failed. Fix the error above before writing to Snowflake.")

print("-" * 40)
staging_path = os.path.join(os.path.dirname(__file__), "predictions_staging.csv")
df = pd.read_csv(staging_path, parse_dates=["PREDICTION_DATE", "SCORED_AT"])
print(f"\n  Read {len(df)} predictions from predictions_staging.csv")


# ── 2. Ensure the target table exists ────────────────────────────────────────
# We use CREATE TABLE IF NOT EXISTS so this script is safe to run repeatedly.
# The table is created once; every subsequent run just appends rows.
print("\n[2/3] Ensuring ML_PREDICTIONS table exists in Snowflake...")

conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)

conn.execute_string(f"""
    CREATE TABLE IF NOT EXISTS {TARGET_DATABASE}.{TARGET_SCHEMA}.{TARGET_TABLE} (
        OPPORTUNITY_ID        VARCHAR(50),
        PREDICTION_DATE       DATE,
        MODEL_VERSION         VARCHAR(20),
        WIN_PROBABILITY       FLOAT,
        WIN_PREDICTED         BOOLEAN,
        PROBABILITY_BAND      VARCHAR(10),
        TOP_POSITIVE_FACTORS  VARCHAR(500),
        TOP_NEGATIVE_FACTORS  VARCHAR(500),
        SCORED_AT             TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
    )
""")
print(f"  Table {TARGET_DATABASE}.{TARGET_SCHEMA}.{TARGET_TABLE} is ready")


# ── 3. Write predictions ──────────────────────────────────────────────────────
# LEARNING NOTE — column name casing:
#   Snowflake stores column names in UPPERCASE by default.
#   write_pandas() maps DataFrame column names to table columns case-insensitively,
#   so our uppercase DataFrame columns match the table definition exactly.
print(f"\n[3/3] Writing {len(df)} rows to {TARGET_TABLE}...")

# Type coercions before writing — pandas internal types don't always map
# cleanly to Snowflake types via write_pandas:
#   PREDICTION_DATE: pandas stores dates as nanosecond Timestamps; Snowflake
#                    DATE expects a string like '2026-05-11' or a Python date.
#   SCORED_AT:       same issue with TIMESTAMP_NTZ.
#   WIN_PREDICTED:   CSV round-trip may read True/False as strings.
df["WIN_PREDICTED"]   = df["WIN_PREDICTED"].astype(bool)
df["PREDICTION_DATE"] = pd.to_datetime(df["PREDICTION_DATE"]).dt.strftime("%Y-%m-%d")
df["SCORED_AT"]       = pd.to_datetime(df["SCORED_AT"]).dt.strftime("%Y-%m-%d %H:%M:%S")

success, n_chunks, n_rows, _ = write_pandas(
    conn=conn,
    df=df,
    table_name=TARGET_TABLE,
    database=TARGET_DATABASE,
    schema=TARGET_SCHEMA,
    overwrite=False,        # append — never overwrite historical predictions
    quote_identifiers=False,
)
conn.close()

if success:
    print(f"  Written    : {n_rows} rows in {n_chunks} chunk(s)")
    print(f"  Table      : {TARGET_DATABASE}.{TARGET_SCHEMA}.{TARGET_TABLE}")
    print(f"  Mode       : APPEND  (history preserved)")
else:
    raise RuntimeError("write_pandas() reported failure — check Snowflake logs")


# ── Summary ───────────────────────────────────────────────────────────────────
band_counts = df["PROBABILITY_BAND"].value_counts()
print("\n" + "=" * 60)
print("  WRITE COMPLETE")
print("=" * 60)
print(f"  Rows written to Snowflake : {n_rows}")
print(f"  HIGH confidence deals     : {band_counts.get('HIGH', 0)}")
print(f"  MEDIUM confidence deals   : {band_counts.get('MEDIUM', 0)}")
print(f"  LOW / at-risk deals       : {band_counts.get('LOW', 0)}")
print()
print("  NEXT STEP: run dbt to refresh the mart layer")
print("    dbt run --select fact_opportunities_scored")
print("  Then connect Power BI to GOLD.FACT_OPPORTUNITIES_SCORED")
print("=" * 60)
