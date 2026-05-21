"""
Configuration for the LLM-RAG layer.
All credentials come from environment variables — never hard-coded.
Create a .env file in the project root:

    SNOWFLAKE_USER=your_user
    SNOWFLAKE_PASSWORD=your_password
    SNOWFLAKE_ACCOUNT=your_account
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Snowflake ────────────────────────────────────────────────────────────────
SNOWFLAKE_CONFIG = {
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": "COMPUTE_WH",
    "database":  "SALES_WIN_DB",
    "schema":    "ML",
}

# ── Embedding model (sentence-transformers, runs locally, no API key) ────────
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
EMBEDDING_DIM     = 384   # all-MiniLM-L6-v2 output dimension

# ── ChromaDB (local persistent vector store) ─────────────────────────────────
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
CHROMA_COLLECTION  = "crm_deals"

# ── Ollama (local LLM — must have ollama installed and running) ───────────────
OLLAMA_MODEL       = "llama3.2:3b"   # change to "mistral:7b" if you have 16GB RAM
OLLAMA_HOST        = "http://localhost:11434"

# ── RAG retrieval settings ────────────────────────────────────────────────────
TOP_K_SIMILAR_DEALS = 12   # how many historical deals to retrieve per query

# ── Snowflake output tables ───────────────────────────────────────────────────
LLM_PREDICTIONS_TABLE  = "LLM_PREDICTIONS"
COMPARISON_TABLE       = "MODEL_COMPARISON"

# ── Source table ─────────────────────────────────────────────────────────────
FEATURE_TABLE = "ML_DEAL_FEATURES"
