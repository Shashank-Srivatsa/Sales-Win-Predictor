"""
04_batch_score_llm.py
---------------------
Scores all open deals with the LLM-RAG predictor.
Writes results to SALES_WIN_DB.ML.LLM_PREDICTIONS.
Expected runtime: ~30 seconds per deal (llama3.2:3b on CPU).
For 50 open deals: ~25 minutes. Run overnight or on a GPU machine.
"""
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from tqdm import tqdm
import sys, os, logging
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from config_llm import SNOWFLAKE_CONFIG, LLM_PREDICTIONS_TABLE
from rag_predict import predict_single

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def batch_score():
    # ── Load open deals ──────────────────────────────────────────────────────
    log.info("Loading open deals from Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    df   = pd.read_sql(
        "SELECT * FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES WHERE TARGET_IS_WON IS NULL",
        conn
    )
    conn.close()
    log.info(f"Found {len(df):,} open deals to score")

    if df.empty:
        log.warning("No open deals found. Exiting.")
        return

    # ── Score each deal ───────────────────────────────────────────────────────
    results = []
    errors  = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Scoring with LLM"):
        try:
            result = predict_single(row.to_dict())
            result["prediction_date"] = str(date.today())
            results.append(result)
        except Exception as e:
            log.error(f"Failed on {row.get('OPPORTUNITY_ID', idx)}: {e}")
            errors.append({"opportunity_id": str(row.get("OPPORTUNITY_ID", idx)), "error": str(e)})

    log.info(f"Scored: {len(results):,}  Errors: {len(errors):,}")

    # ── Write to Snowflake ───────────────────────────────────────────────────
    if results:
        results_df = pd.DataFrame(results)
        results_df.columns = [c.upper() for c in results_df.columns]

        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        write_pandas(
            conn,
            results_df,
            LLM_PREDICTIONS_TABLE,
            database="SALES_WIN_DB",
            schema="ML",
            overwrite=False,
            auto_create_table=False,
        )
        conn.close()
        log.info(f"Written {len(results_df):,} rows to SALES_WIN_DB.ML.{LLM_PREDICTIONS_TABLE}")

    if errors:
        log.warning(f"{len(errors)} deals failed — check logs above for details")


if __name__ == "__main__":
    batch_score()
