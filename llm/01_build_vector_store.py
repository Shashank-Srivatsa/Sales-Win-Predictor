"""
01_build_vector_store.py
------------------------
Reads all closed deals from Snowflake, serialises them to text,
embeds them, and stores in ChromaDB.

Run once to build the store, then again periodically to add new closed deals.
Runtime: ~2-3 minutes for 1,000 deals on a modern laptop.
"""
import chromadb
import pandas as pd
import snowflake.connector
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from config_llm import SNOWFLAKE_CONFIG, EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_COLLECTION
from serialise_deal import serialise_deal


def build_vector_store():
    # ── 1. Load closed deals from Snowflake ─────────────────────────────────
    print("Connecting to Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    df   = pd.read_sql(
        """
        SELECT *
        FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
        WHERE TARGET_IS_WON IS NOT NULL
        ORDER BY FISCAL_YEAR ASC
        """,
        conn
    )
    conn.close()
    print(f"Loaded {len(df):,} closed deals (Won: {(df['TARGET_IS_WON']==1).sum():,}, Lost: {(df['TARGET_IS_WON']==0).sum():,})")

    # ── 2. Load embedding model (downloads ~22MB on first run) ──────────────
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    # ── 3. Initialise ChromaDB ───────────────────────────────────────────────
    print(f"\nInitialising ChromaDB at: {CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    # ── 4. Embed and store in batches ────────────────────────────────────────
    BATCH_SIZE = 100
    records    = df.to_dict("records")

    for batch_start in tqdm(range(0, len(records), BATCH_SIZE), desc="Embedding deals"):
        batch = records[batch_start : batch_start + BATCH_SIZE]

        texts      = [serialise_deal(row) for row in batch]
        ids        = [str(row["OPPORTUNITY_ID"]) for row in batch]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        metadatas = [
            {
                "opportunity_id": str(row["OPPORTUNITY_ID"]),
                "is_won":         int(row["TARGET_IS_WON"]),
                "division":       int(row.get("DIVISION_ENCODED", 0)),
                "deal_value":     float(row.get("DEAL_VALUE_RAW", 0)),
                "discount_pct":   float(row.get("DISCOUNT_PCT", 0)),
                "fiscal_year":    int(row.get("FISCAL_YEAR", 2020)),
                "agent_win_rate": float(row.get("AGENT_TRAILING_12M_WIN_RATE", 0.4)),
            }
            for row in batch
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    print(f"\nVector store built. Total documents: {collection.count()}")
    print(f"Persisted to: {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    build_vector_store()
