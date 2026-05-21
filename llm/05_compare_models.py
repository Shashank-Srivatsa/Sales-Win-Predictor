"""
05_compare_models.py
--------------------
Joins XGBoost and LLM predictions, computes agreement/disagreement metrics,
writes to SALES_WIN_DB.ML.MODEL_COMPARISON.

Key insight: When XGBoost says 0.80 and LLM says 0.30, that disagreement
IS the signal — it means the deal has something unusual the numbers capture
differently than the LLM's business reasoning. Flag these for human review.
"""
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import sys, os, logging
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from config_llm import SNOWFLAKE_CONFIG, COMPARISON_TABLE

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def compare_models():
    log.info("Loading predictions from Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)

    xgb_df = pd.read_sql(
        """
        SELECT
            OPPORTUNITY_ID,
            WIN_PROBABILITY      AS XGB_WIN_PROBABILITY,
            PROBABILITY_BAND     AS XGB_PROBABILITY_BAND
        FROM SALES_WIN_DB.ML.ML_PREDICTIONS
        """,
        conn
    )

    llm_df = pd.read_sql(
        """
        SELECT
            OPPORTUNITY_ID,
            LLM_WIN_PROBABILITY,
            LLM_PROBABILITY_BAND,
            LLM_REASONING
        FROM SALES_WIN_DB.ML.LLM_PREDICTIONS
        """,
        conn
    )
    conn.close()

    log.info(f"XGBoost predictions: {len(xgb_df):,}  LLM predictions: {len(llm_df):,}")

    if xgb_df.empty or llm_df.empty:
        log.warning("One or both prediction tables are empty. Exiting.")
        return

    # ── Join on opportunity_id ────────────────────────────────────────────────
    comparison_df = xgb_df.merge(llm_df, on="OPPORTUNITY_ID", how="inner")
    log.info(f"Joined on OPPORTUNITY_ID: {len(comparison_df):,} rows")

    # ── Compute comparison metrics ────────────────────────────────────────────
    comparison_df["PROBABILITY_DELTA"] = (
        comparison_df["XGB_WIN_PROBABILITY"] - comparison_df["LLM_WIN_PROBABILITY"]
    ).abs()

    comparison_df["MODELS_AGREE"] = (
        comparison_df["XGB_PROBABILITY_BAND"] == comparison_df["LLM_PROBABILITY_BAND"]
    )

    comparison_df["DISAGREEMENT_FLAG"] = comparison_df["PROBABILITY_DELTA"] > 0.25

    comparison_df["HIGHER_CONFIDENCE_MODEL"] = comparison_df.apply(
        lambda r: "XGB"
        if abs(r["XGB_WIN_PROBABILITY"] - 0.5) > abs(r["LLM_WIN_PROBABILITY"] - 0.5)
        else "LLM",
        axis=1,
    )

    comparison_df["COMPARISON_DATE"] = str(date.today())

    # ── Rename to match Snowflake schema ─────────────────────────────────────
    output_df = comparison_df[[
        "OPPORTUNITY_ID",
        "COMPARISON_DATE",
        "XGB_WIN_PROBABILITY",
        "XGB_PROBABILITY_BAND",
        "LLM_WIN_PROBABILITY",
        "LLM_PROBABILITY_BAND",
        "PROBABILITY_DELTA",
        "MODELS_AGREE",
        "DISAGREEMENT_FLAG",
        "HIGHER_CONFIDENCE_MODEL",
        "LLM_REASONING",
    ]]

    agree_pct = output_df["MODELS_AGREE"].mean() * 100
    disagree_count = output_df["DISAGREEMENT_FLAG"].sum()
    log.info(f"Model agreement rate: {agree_pct:.1f}%")
    log.info(f"High-disagreement deals (delta > 0.25): {disagree_count}")

    # ── Write to Snowflake ────────────────────────────────────────────────────
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    write_pandas(
        conn,
        output_df,
        COMPARISON_TABLE,
        database="SALES_WIN_DB",
        schema="ML",
        overwrite=True,
        auto_create_table=False,
    )
    conn.close()
    log.info(f"Written {len(output_df):,} rows to SALES_WIN_DB.ML.{COMPARISON_TABLE}")


if __name__ == "__main__":
    compare_models()
