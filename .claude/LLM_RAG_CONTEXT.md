# LLM-RAG Layer — Claude Code Context File
# Sales Win Predictor · Phase 2

> **Purpose of this file:** Claude Code should read this entire file before writing a single line of
> code. It describes exactly what to build, where it lives in the existing project, what tools to
> use, what every file must do, and what the inputs and outputs are at every step.
>
> **Free tools only.** No OpenAI API. No Pinecone. No paid services of any kind.
> Every library used here has a free tier or is fully open-source.

---

## 0. What Already Exists (Do Not Touch)

The existing project at `Shashank-Srivatsa/Sales-Win-Predictor` has this structure:

```
Sales-Win-Predictor/
├── .claude/                        ← Claude Code config (leave as-is)
├── Data-Ingestion/                 ← Bronze ingestion scripts (leave as-is)
├── Documentation/                  ← Project docs (leave as-is)
├── Sales_Report.Report/            ← Power BI report folder (leave as-is)
├── logs/                           ← Log files (leave as-is)
├── ml/                             ← XGBoost pipeline (DO NOT MODIFY)
│   ├── config.py
│   ├── 01_eda.py
│   ├── 02_train.py
│   ├── 03_evaluate.py
│   ├── 04_explain.py               ← SHAP
│   ├── 05_score.py
│   └── 06_write_predictions.py     ← writes to ML.ML_PREDICTIONS
├── sales_win_predictor/            ← dbt project (leave as-is)
├── GenerateCRMData.py
├── requirements.txt
├── Sales_Report.pbip
└── README.md
```

### What Phase 1 (existing) Produced in Snowflake

```
SALES_WIN_DB
├── BRONZE      ← raw CRM CSVs (9 tables)
├── SILVER      ← dbt staging + intermediate views
├── GOLD        ← dbt mart tables (fact_opportunities, dim_*, fact_stage_history)
└── ML
    ├── ML_DEAL_FEATURES        ← feature table (one row per deal, 30+ columns)
    └── ML_PREDICTIONS          ← XGBoost win probability per open deal
```

The `ML_DEAL_FEATURES` table is the **starting point** for everything in Phase 2.

---

## 1. What Phase 2 Builds (The LLM-RAG Layer)

Phase 2 adds a **new folder** called `llm/` to the root of the repo. It does not touch `ml/` at all.

```
Sales-Win-Predictor/
└── llm/                            ← CREATE THIS — everything in Phase 2 lives here
    ├── requirements_llm.txt
    ├── config_llm.py
    ├── 01_build_vector_store.py    ← embed historical deals → ChromaDB
    ├── 02_serialise_deal.py        ← convert a deal row to natural language text
    ├── 03_rag_predict.py           ← similarity search + Ollama LLM → probability
    ├── 04_batch_score_llm.py       ← score all open deals, write to Snowflake
    ├── 05_compare_models.py        ← XGBoost vs LLM comparison table
    ├── prompts/
    │   └── win_predictor.txt       ← the master prompt template
    └── chroma_db/                  ← ChromaDB persisted vector store (git-ignored)
```

### New Snowflake Table Phase 2 Creates

```sql
SALES_WIN_DB.ML.LLM_PREDICTIONS
```

Fields defined in Section 7.

### The End-to-End Flow for Phase 2

```
ML.ML_DEAL_FEATURES
        │
        ▼
[01_build_vector_store.py]
  • Read all CLOSED deals (is_won IS NOT NULL)
  • Serialise each deal to text  ──► [02_serialise_deal.py]
  • Embed text with sentence-transformers (free, local)
  • Store embeddings + metadata in ChromaDB (free, local)
        │
        ▼
ChromaDB (persisted to llm/chroma_db/)
        │
        │  For each OPEN deal:
        ▼
[03_rag_predict.py]
  • Serialise the open deal to text
  • Embed it
  • Similarity search: retrieve top 12 most similar CLOSED deals
  • Build prompt: 12 examples (with outcomes) + new deal
  • Send to Ollama (free, local LLM — llama3.2 or mistral)
  • Parse probability + reasoning from response
        │
        ▼
[04_batch_score_llm.py]
  • Loop all open deals through 03_rag_predict.py
  • Write results to SALES_WIN_DB.ML.LLM_PREDICTIONS
        │
        ▼
[05_compare_models.py]
  • Join ML_PREDICTIONS + LLM_PREDICTIONS on opportunity_id
  • Compute agreement rate, disagreement cases
  • Write comparison to SALES_WIN_DB.ML.MODEL_COMPARISON
```

---

## 2. Free Tool Stack

| Need | Tool | Why Free | Install |
|---|---|---|---|
| Text embeddings | `sentence-transformers` | Fully open-source, runs locally, no API key | `pip install sentence-transformers` |
| Embedding model | `all-MiniLM-L6-v2` | 22MB, fast, good quality, downloads automatically | Auto-downloaded by sentence-transformers |
| Vector database | `chromadb` | Open-source, runs in-process, persists to disk | `pip install chromadb` |
| Local LLM inference | `ollama` | Free, runs LLMs locally on your machine | https://ollama.com (one-click installer) |
| LLM model | `llama3.2:3b` or `mistral:7b` | Free weights, pulled via ollama | `ollama pull llama3.2:3b` |
| Ollama Python client | `ollama` Python package | Free | `pip install ollama` |
| Snowflake connector | `snowflake-connector-python` | Already in requirements.txt | Already installed |
| Data manipulation | `pandas`, `numpy` | Already in requirements.txt | Already installed |

### Why Ollama (not OpenAI)

Ollama runs LLMs **completely on your local machine**. No internet. No API key. No cost per token.
`llama3.2:3b` needs ~4GB RAM. `mistral:7b` needs ~8GB RAM. Use `llama3.2:3b` if RAM is limited.

### System Requirements for Ollama

- Windows 10/11, macOS 12+, or Linux
- Minimum 8GB RAM (llama3.2:3b works on 8GB; mistral:7b needs 16GB ideally)
- Ollama must be running before any LLM script executes: `ollama serve`

---

## 3. The requirements_llm.txt File

```
sentence-transformers==2.7.0
chromadb==0.5.3
ollama==0.2.1
pandas
numpy
snowflake-connector-python[pandas]
python-dotenv
tqdm
```

Install with: `pip install -r llm/requirements_llm.txt`

---

## 4. config_llm.py

```python
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
                            # 12 is a good balance: enough context, fits in context window

# ── Snowflake output tables ───────────────────────────────────────────────────
LLM_PREDICTIONS_TABLE  = "LLM_PREDICTIONS"
COMPARISON_TABLE       = "MODEL_COMPARISON"

# ── Source table ─────────────────────────────────────────────────────────────
FEATURE_TABLE = "ML_DEAL_FEATURES"
```

---

## 5. The ML_DEAL_FEATURES Table (Input — What We Read)

This table lives in `SALES_WIN_DB.ML.ML_DEAL_FEATURES`.
It was created by the dbt `ml/` models in Phase 1.

**Columns used in Phase 2:**

| Column | Type | Used For |
|---|---|---|
| `OPPORTUNITY_ID` | VARCHAR | Unique identifier — stored as ChromaDB document ID |
| `TARGET` | NUMBER | 1=Won, 0=Lost, NULL=open. Filter: historical = NOT NULL, scoring = NULL |
| `DEAL_VALUE_RAW` | FLOAT | Text serialisation |
| `DISCOUNT_PCT` | FLOAT | Text serialisation + key signal |
| `DISCOUNT_RISK_SCORE` | FLOAT | Text serialisation |
| `IS_RENEWAL` | NUMBER | Text serialisation |
| `DEAL_TYPE_ENCODED` | NUMBER | Decoded back to label in serialisation |
| `DIVISION_ENCODED` | NUMBER | Decoded back to label in serialisation |
| `REGION_ENCODED` | NUMBER | Decoded back to label in serialisation |
| `TOTAL_DAYS_IN_FUNNEL` | FLOAT | Text serialisation |
| `DAYS_IN_NEGOTIATION_STAGE` | FLOAT | Text serialisation — key risk signal |
| `IS_FISCAL_QUARTER_END_PERIOD` | NUMBER | Text serialisation |
| `LINE_ITEM_COUNT` | FLOAT | Text serialisation |
| `DEAL_COMPLEXITY_SCORE` | FLOAT | Text serialisation |
| `DEAL_VELOCITY_SCORE` | FLOAT | Text serialisation |
| `AGENT_TRAILING_12M_WIN_RATE` | FLOAT | Text serialisation — strongest agent signal |
| `AGENT_SENIORITY_LEVEL` | FLOAT | Text serialisation |
| `AGENT_CURRENT_OPEN_DEALS` | FLOAT | Text serialisation |
| `IS_VERTICAL_SPECIALIST` | FLOAT | Text serialisation |
| `CLIENT_WIN_RATE` | FLOAT | Text serialisation |
| `CLIENT_IS_NEW` | FLOAT | Text serialisation |
| `CLIENT_DAYS_SINCE_LAST_DEAL` | FLOAT | Text serialisation |
| `ACCOUNT_TIER` | FLOAT | Text serialisation |
| `TOTAL_ACTIVITIES` | FLOAT | Text serialisation |
| `DAYS_SINCE_LAST_ACTIVITY` | FLOAT | Text serialisation |
| `ENGAGEMENT_SCORE` | FLOAT | Text serialisation |
| `POSITIVE_ACTIVITY_RATIO` | FLOAT | Text serialisation |
| `STAGE_REGRESSION_COUNT` | FLOAT | Text serialisation |
| `CONTRACT_REVISION_COUNT` | FLOAT | Text serialisation |
| `FISCAL_YEAR` | NUMBER | Used for metadata filtering |
| `FISCAL_QUARTER` | VARCHAR | Metadata |

---

## 6. The Deal Serialiser (02_serialise_deal.py)

### What it Does

Converts one row of the feature table into a **natural language paragraph** that a human (or LLM) can read and reason about. This is the most important design decision in the whole layer.

The LLM cannot read numbers directly in a meaningful way — `discount_pct = 31` means nothing on its own. But "a discount of 31%, which is well above the 20% threshold where win rates drop sharply" gives the LLM the business context it needs to reason.

### Decoding Maps (hard-code these exactly)

```python
DIVISION_MAP = {0: "TalentEdge", 1: "CreativeMotion", 2: "PulseMedia", 3: "BrandVault"}
REGION_MAP   = {0: "North America", 1: "Europe", 2: "India", 3: "Asia Pacific", 4: "Australia"}
DEAL_TYPE_MAP= {0: "New Business", 1: "Renewal", 2: "Upsell", 3: "Cross-sell"}
SENIORITY_MAP= {1: "Junior", 2: "Mid-level", 3: "Senior", 4: "Director", 5: "VP/Head"}
TIER_MAP     = {1: "Tier 1 (top client)", 2: "Tier 2 (mid-tier)", 3: "Tier 3 (small/new)"}
```

### The Serialise Function

```python
def serialise_deal(row: dict) -> str:
    """
    Convert one deal's feature row into a natural language description.
    row: a dictionary of {column_name: value} for one deal.
    Returns: a multi-line string describing the deal in business language.
    """
    division    = DIVISION_MAP.get(int(row.get("DIVISION_ENCODED", 0)), "Unknown")
    region      = REGION_MAP.get(int(row.get("REGION_ENCODED", 0)), "Unknown")
    deal_type   = DEAL_TYPE_MAP.get(int(row.get("DEAL_TYPE_ENCODED", 0)), "New Business")
    seniority   = SENIORITY_MAP.get(int(row.get("AGENT_SENIORITY_LEVEL", 2)), "Mid-level")
    tier        = TIER_MAP.get(int(row.get("ACCOUNT_TIER", 3)), "Tier 3 (small/new)")

    discount    = float(row.get("DISCOUNT_PCT", 0))
    disc_signal = (
        "well below the safe threshold — strong pricing"  if discount < 10 else
        "within the acceptable range"                     if discount < 20 else
        "above the 20% warning level"                     if discount < 30 else
        "critically high — historically predicts loss"
    )

    velocity    = float(row.get("DEAL_VELOCITY_SCORE", 1.0))
    vel_signal  = (
        "moving faster than average — positive momentum"    if velocity > 1.1 else
        "moving at average pace"                            if velocity > 0.8 else
        "moving slower than average — risk of stalling"     if velocity > 0.5 else
        "critically slow — significantly behind average pace"
    )

    agent_wr    = float(row.get("AGENT_TRAILING_12M_WIN_RATE", 0.4))
    agent_signal= (
        "excellent (above 50%)"    if agent_wr > 0.50 else
        "above average (40-50%)"   if agent_wr > 0.40 else
        "below average (30-40%)"   if agent_wr > 0.30 else
        "poor (below 30%)"
    )

    days_neg    = float(row.get("DAYS_IN_NEGOTIATION_STAGE", 0))
    neg_signal  = (
        "fast negotiation — positive"    if days_neg < 10 else
        "normal negotiation pace"        if days_neg < 21 else
        "negotiation is running long"    if days_neg < 35 else
        "negotiation is critically stalled"
    )

    engagement  = float(row.get("ENGAGEMENT_SCORE", 0.5))
    eng_signal  = (
        "client is highly engaged recently"   if engagement > 0.6 else
        "client engagement is moderate"       if engagement > 0.3 else
        "client engagement is dropping off — possible disengagement"
    )

    is_renewal    = int(row.get("IS_RENEWAL", 0))
    is_specialist = int(row.get("IS_VERTICAL_SPECIALIST", 0))
    is_new_client = int(row.get("CLIENT_IS_NEW", 0))
    regressions   = int(row.get("STAGE_REGRESSION_COUNT", 0))
    revisions     = int(row.get("CONTRACT_REVISION_COUNT", 0))
    qtr_end       = int(row.get("IS_FISCAL_QUARTER_END_PERIOD", 0))

    text = f"""
DEAL SUMMARY:
Division: {division}
Region: {region}
Deal Type: {deal_type} {"(this is a renewal — client has bought before)" if is_renewal else ""}
Deal Value: ${float(row.get('DEAL_VALUE_RAW', 0)):,.0f}
Discount Offered: {discount:.1f}% — {disc_signal}
Total Days in Pipeline: {int(float(row.get('TOTAL_DAYS_IN_FUNNEL', 0)))} days
Days in Negotiation Stage: {int(days_neg)} days — {neg_signal}
Deal Velocity: {velocity:.2f} — {vel_signal}
Line Item Count: {int(float(row.get('LINE_ITEM_COUNT', 0)))} items
Deal Complexity Score: {float(row.get('DEAL_COMPLEXITY_SCORE', 0)):.1f}
Stage Regressions: {regressions} {"(deal moved backwards in the funnel)" if regressions > 0 else ""}
Contract Revisions: {revisions} {"(high revision count — client is not committed)" if revisions > 3 else ""}
Fiscal Quarter End Approaching: {"Yes — urgency pressure to close" if qtr_end else "No"}

AGENT PROFILE:
Seniority: {seniority}
Trailing 12-Month Win Rate: {agent_wr:.0%} — {agent_signal}
Current Open Deals (workload): {int(float(row.get('AGENT_CURRENT_OPEN_DEALS', 0)))}
Is Division Specialist: {"Yes" if is_specialist else "No — agent is working outside their primary division"}

CLIENT PROFILE:
Client Tier: {tier}
Is New Client: {"Yes — no prior won deals (new clients win at ~30% vs ~52% for repeat)" if is_new_client else "No — existing relationship"}
Client Historical Win Rate: {float(row.get('CLIENT_WIN_RATE', 0)):.0%}
Days Since Last Closed Deal: {int(float(row.get('CLIENT_DAYS_SINCE_LAST_DEAL', 0)))}

ENGAGEMENT SIGNALS:
Total Activities Logged: {int(float(row.get('TOTAL_ACTIVITIES', 0)))}
Days Since Last Client Contact: {int(float(row.get('DAYS_SINCE_LAST_ACTIVITY', 0)))}
Client Engagement Score: {engagement:.2f} — {eng_signal}
Positive Activity Ratio: {float(row.get('POSITIVE_ACTIVITY_RATIO', 0)):.0%}
""".strip()

    return text
```

---

## 7. The Vector Store Builder (01_build_vector_store.py)

### What it Does

1. Reads all **closed** deals from `ML.ML_DEAL_FEATURES` (`TARGET IS NOT NULL`)
2. Serialises each to text using `serialise_deal()`
3. Embeds each text using `sentence-transformers` (`all-MiniLM-L6-v2`)
4. Stores the vectors + metadata + outcome in **ChromaDB** (persisted to `llm/chroma_db/`)

This only needs to run **once** (and again when new closed deals are added).

### Full Script

```python
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
from serialise_deal import serialise_deal   # NOTE: import from 02_serialise_deal.py
                                              # rename function file to serialise_deal.py

def build_vector_store():
    # ── 1. Load closed deals from Snowflake ─────────────────────────────────
    print("Connecting to Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    df   = pd.read_sql(
        """
        SELECT *
        FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES
        WHERE TARGET IS NOT NULL
        ORDER BY FISCAL_YEAR ASC
        """,
        conn
    )
    conn.close()
    print(f"Loaded {len(df):,} closed deals (Won: {(df['TARGET']==1).sum():,}, Lost: {(df['TARGET']==0).sum():,})")

    # ── 2. Load embedding model (downloads ~22MB on first run) ──────────────
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    # ── 3. Initialise ChromaDB ───────────────────────────────────────────────
    print(f"\nInitialising ChromaDB at: {CHROMA_PERSIST_DIR}")
    client     = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    # Delete and recreate to ensure clean rebuild
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for text embeddings
    )

    # ── 4. Embed and store in batches ────────────────────────────────────────
    BATCH_SIZE = 100
    records    = df.to_dict("records")

    for batch_start in tqdm(range(0, len(records), BATCH_SIZE), desc="Embedding deals"):
        batch = records[batch_start : batch_start + BATCH_SIZE]

        texts    = [serialise_deal(row) for row in batch]
        ids      = [str(row["OPPORTUNITY_ID"]) for row in batch]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        # Metadata stored alongside each vector (used for filtering and display)
        metadatas = [
            {
                "opportunity_id":   str(row["OPPORTUNITY_ID"]),
                "is_won":           int(row["TARGET"]),
                "division":         int(row.get("DIVISION_ENCODED", 0)),
                "deal_value":       float(row.get("DEAL_VALUE_RAW", 0)),
                "discount_pct":     float(row.get("DISCOUNT_PCT", 0)),
                "fiscal_year":      int(row.get("FISCAL_YEAR", 2020)),
                "agent_win_rate":   float(row.get("AGENT_TRAILING_12M_WIN_RATE", 0.4)),
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
```

---

## 8. The RAG Predictor (03_rag_predict.py)

### What it Does

For a single deal row, this module:
1. Serialises it to text
2. Embeds it
3. Retrieves the 12 most similar historical deals from ChromaDB
4. Builds a structured prompt (few-shot examples + new deal)
5. Calls Ollama (local LLM) for prediction
6. Parses the probability and reasoning from the response

### The Prompt Template (prompts/win_predictor.txt)

Claude Code must create this file at `llm/prompts/win_predictor.txt`:

```
You are an expert sales analyst at a global talent and brand management company.
Your job is to predict the probability that a CRM deal will be WON, based on deal characteristics.

You will be given {n_examples} examples of past deals and their actual outcomes.
Study them carefully — they come from the same business and represent real patterns.

Then you will be given a NEW deal to evaluate.

IMPORTANT INSTRUCTIONS:
- Return your answer in EXACTLY this format, on two separate lines:
  PROBABILITY: [a number between 0.00 and 1.00]
  REASONING: [2-3 sentences explaining the key factors]
- The probability must be a decimal number like 0.72 or 0.35
- Do not add any other text before or after these two lines
- Base your reasoning on the specific details provided, not generic statements

---

PAST DEAL EXAMPLES:
{examples_block}

---

NEW DEAL TO EVALUATE:
{new_deal_text}

---

Your prediction:
```

### The predict_single Function

```python
"""
03_rag_predict.py
-----------------
Given one deal (as a dict from ML_DEAL_FEATURES), returns:
  - llm_win_probability (float 0.0–1.0)
  - llm_reasoning (string)
  - similar_deals_used (list of opportunity_ids retrieved)
"""
import re, os, sys
import chromadb
import ollama
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.dirname(__file__))
from config_llm import (
    EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_COLLECTION,
    OLLAMA_MODEL, OLLAMA_HOST, TOP_K_SIMILAR_DEALS
)
from serialise_deal import serialise_deal

# ── Module-level singletons (loaded once, reused for all deals) ───────────────
_embedder   = None
_collection = None
_prompt_tpl = None

def _load_resources():
    global _embedder, _collection, _prompt_tpl
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    if _collection is None:
        client      = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = client.get_collection(CHROMA_COLLECTION)
    if _prompt_tpl is None:
        tpl_path    = os.path.join(os.path.dirname(__file__), "prompts", "win_predictor.txt")
        with open(tpl_path, "r") as f:
            _prompt_tpl = f.read()


def _build_examples_block(similar_docs: list, similar_metas: list) -> str:
    """
    Build the few-shot examples section of the prompt.
    similar_docs : list of deal text descriptions (retrieved from ChromaDB)
    similar_metas: list of metadata dicts (contains is_won, deal_value etc.)
    """
    blocks = []
    for i, (doc, meta) in enumerate(zip(similar_docs, similar_metas), 1):
        outcome = "WON" if meta["is_won"] == 1 else "LOST"
        blocks.append(f"EXAMPLE {i} — OUTCOME: {outcome}\n{doc}")
    return "\n\n---\n\n".join(blocks)


def _parse_response(response_text: str) -> tuple[float, str]:
    """
    Extract probability and reasoning from the LLM response.
    Returns (probability, reasoning). Defaults to 0.5 if parsing fails.
    """
    probability = 0.5   # safe default
    reasoning   = response_text.strip()

    # Find PROBABILITY: line
    prob_match = re.search(
        r"PROBABILITY:\s*([0-9]+\.?[0-9]*)",
        response_text, re.IGNORECASE
    )
    if prob_match:
        raw = float(prob_match.group(1))
        # Handle if model writes 72 instead of 0.72
        probability = raw / 100.0 if raw > 1.0 else raw
        probability = max(0.01, min(0.99, probability))   # clamp to valid range

    # Find REASONING: line
    reason_match = re.search(
        r"REASONING:\s*(.+?)(?=\n[A-Z]+:|$)",
        response_text, re.IGNORECASE | re.DOTALL
    )
    if reason_match:
        reasoning = reason_match.group(1).strip()

    return probability, reasoning


def predict_single(deal_row: dict) -> dict:
    """
    Main function. Predicts win probability for one deal using RAG + Ollama.

    Parameters
    ----------
    deal_row : dict
        One row from ML_DEAL_FEATURES as a Python dict.
        Keys are Snowflake column names (uppercase).

    Returns
    -------
    dict with keys:
        opportunity_id      : str
        llm_win_probability : float (0.0–1.0)
        llm_probability_band: str  (HIGH / MEDIUM / LOW)
        llm_reasoning       : str
        similar_deals_count : int
        similar_deal_ids    : str  (comma-separated)
        llm_model_used      : str
    """
    _load_resources()

    opp_id   = str(deal_row.get("OPPORTUNITY_ID", "UNKNOWN"))
    deal_text = serialise_deal(deal_row)

    # ── Step 1: Embed the new deal ───────────────────────────────────────────
    query_embedding = _embedder.encode(deal_text).tolist()

    # ── Step 2: Retrieve top K similar historical deals ──────────────────────
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K_SIMILAR_DEALS,
        include=["documents", "metadatas", "distances"],
    )
    similar_docs   = results["documents"][0]
    similar_metas  = results["metadatas"][0]
    similar_ids    = [m["opportunity_id"] for m in similar_metas]

    # ── Step 3: Build the prompt ─────────────────────────────────────────────
    examples_block = _build_examples_block(similar_docs, similar_metas)
    prompt = _prompt_tpl.format(
        n_examples=TOP_K_SIMILAR_DEALS,
        examples_block=examples_block,
        new_deal_text=deal_text,
    )

    # ── Step 4: Call Ollama (local LLM) ──────────────────────────────────────
    client   = ollama.Client(host=OLLAMA_HOST)
    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={
            "temperature": 0.1,     # low temperature = more deterministic output
            "num_predict": 200,     # max tokens in response
            "stop": ["\n\n\n"],     # stop at triple newline
        },
    )
    response_text = response["response"]

    # ── Step 5: Parse response ────────────────────────────────────────────────
    probability, reasoning = _parse_response(response_text)

    band = (
        "HIGH"   if probability >= 0.70 else
        "MEDIUM" if probability >= 0.40 else
        "LOW"
    )

    return {
        "opportunity_id":       opp_id,
        "llm_win_probability":  round(probability, 4),
        "llm_probability_band": band,
        "llm_reasoning":        reasoning[:1000],   # cap at 1000 chars for Snowflake
        "similar_deals_count":  len(similar_ids),
        "similar_deal_ids":     ",".join(similar_ids[:5]),   # first 5 for traceability
        "llm_model_used":       OLLAMA_MODEL,
        "raw_llm_response":     response_text[:500],   # for debugging
    }
```

---

## 9. Batch Scorer (04_batch_score_llm.py)

### What it Does

Reads all **open** deals from `ML_DEAL_FEATURES`, calls `predict_single()` for each, and writes results to `SALES_WIN_DB.ML.LLM_PREDICTIONS`.

### Create the Output Table First

Before running, create this table in Snowflake:

```sql
CREATE OR REPLACE TABLE SALES_WIN_DB.ML.LLM_PREDICTIONS (
    opportunity_id          VARCHAR(50),
    prediction_date         DATE             DEFAULT CURRENT_DATE,
    llm_model_used          VARCHAR(50),
    llm_win_probability     FLOAT,
    llm_probability_band    VARCHAR(10),     -- HIGH / MEDIUM / LOW
    llm_reasoning           VARCHAR(2000),   -- LLM's explanation
    similar_deals_count     NUMBER,          -- how many examples were retrieved
    similar_deal_ids        VARCHAR(500),    -- first 5 retrieved deal IDs
    raw_llm_response        VARCHAR(1000),   -- for debugging
    scored_at               TIMESTAMP_NTZ    DEFAULT CURRENT_TIMESTAMP
);
```

### The Script

```python
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
from rag_predict import predict_single   # NOTE: import from 03_rag_predict.py

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def batch_score():
    # ── Load open deals ──────────────────────────────────────────────────────
    log.info("Loading open deals from Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    df   = pd.read_sql(
        "SELECT * FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES WHERE TARGET IS NULL",
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
        # Rename columns to match Snowflake table (all uppercase)
        results_df.columns = [c.upper() for c in results_df.columns]

        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        write_pandas(
            conn,
            results_df,
            LLM_PREDICTIONS_TABLE,
            database="SALES_WIN_DB",
            schema="ML",
            overwrite=False,    # append to existing
            auto_create_table=False,
        )
        conn.close()
        log.info(f"Written {len(results_df):,} rows to SALES_WIN_DB.ML.{LLM_PREDICTIONS_TABLE}")

    if errors:
        log.warning(f"{len(errors)} deals failed — check logs above for details")

if __name__ == "__main__":
    batch_score()
```

---

## 10. Model Comparison (05_compare_models.py)

### What it Does

Joins `ML_PREDICTIONS` (XGBoost) and `LLM_PREDICTIONS` (LLM-RAG) on `opportunity_id` and writes a comparison table to `SALES_WIN_DB.ML.MODEL_COMPARISON`.

### Create the Output Table First

```sql
CREATE OR REPLACE TABLE SALES_WIN_DB.ML.MODEL_COMPARISON (
    opportunity_id              VARCHAR(50),
    comparison_date             DATE,
    xgb_win_probability         FLOAT,
    xgb_probability_band        VARCHAR(10),
    llm_win_probability         FLOAT,
    llm_probability_band        VARCHAR(10),
    probability_delta           FLOAT,       -- ABS(xgb - llm)
    models_agree                BOOLEAN,     -- both in same band
    disagreement_flag           BOOLEAN,     -- delta > 0.25 (significant disagreement)
    higher_confidence_model     VARCHAR(10), -- XGB or LLM (whichever is more extreme)
    llm_reasoning               VARCHAR(2000)
);
```

### Logic

```python
"""
05_compare_models.py
--------------------
Joins XGBoost and LLM predictions, computes agreement/disagreement metrics,
writes to SALES_WIN_DB.ML.MODEL_COMPARISON.

Key insight: When XGBoost says 0.80 and LLM says 0.30, that disagreement
IS the signal — it means the deal has something unusual the numbers capture
differently than the LLM's business reasoning. Flag these for human review.
"""
# After joining xgb_df and llm_df on opportunity_id:

comparison_df["PROBABILITY_DELTA"]     = abs(comparison_df["XGB_WIN_PROBABILITY"] - comparison_df["LLM_WIN_PROBABILITY"])
comparison_df["MODELS_AGREE"]          = comparison_df["XGB_PROBABILITY_BAND"] == comparison_df["LLM_PROBABILITY_BAND"]
comparison_df["DISAGREEMENT_FLAG"]     = comparison_df["PROBABILITY_DELTA"] > 0.25
comparison_df["HIGHER_CONFIDENCE_MODEL"] = comparison_df.apply(
    lambda r: "XGB" if abs(r["XGB_WIN_PROBABILITY"] - 0.5) > abs(r["LLM_WIN_PROBABILITY"] - 0.5)
              else "LLM",
    axis=1
)
```

---

## 11. Power BI — New Visuals for Phase 2

These visuals are **additions** to the existing 6-page report. Add them as new pages or as new sections on existing pages.

### New Page 7 — LLM Deal Intelligence

**Purpose:** Show the LLM's natural language reasoning for each deal.

Visuals:
- Deal slicer (dropdown by `opportunity_id` or deal name)
- Card: `LLM_WIN_PROBABILITY` formatted as percentage
- Card: `LLM_PROBABILITY_BAND` with conditional formatting (red/amber/green)
- Text card: `LLM_REASONING` (the LLM's explanation paragraph)
- Comparison bar: XGBoost probability vs LLM probability side by side

### New Page 8 — Model Agreement Dashboard

**Purpose:** Surface the cases where XGBoost and the LLM disagree — those are the most interesting deals.

Visuals:
- KPI: % of deals where models agree (same band)
- KPI: Count of `DISAGREEMENT_FLAG = TRUE` deals
- Table: `opportunity_id`, `XGB_PROBABILITY`, `LLM_PROBABILITY`, `DELTA`, `LLM_REASONING` — filtered to `DISAGREEMENT_FLAG = TRUE`
- Scatter: X = XGB probability, Y = LLM probability — each dot is a deal. Dots far from the diagonal line = disagreement.

### New DAX Measures

```dax
-- Agreement Rate
Model Agreement Rate =
    DIVIDE(
        COUNTROWS(FILTER('MODEL_COMPARISON', [MODELS_AGREE] = TRUE)),
        COUNTROWS('MODEL_COMPARISON')
    )

-- Disagreement Count
High Disagreement Deals =
    COUNTROWS(FILTER('MODEL_COMPARISON', [DISAGREEMENT_FLAG] = TRUE))

-- LLM Weighted Pipeline
LLM Weighted Pipeline =
    SUMX(
        'LLM_PREDICTIONS',
        RELATED('fact_opportunities'[amount]) * [LLM_WIN_PROBABILITY]
    )
```

---

## 12. File Naming — Important for Claude Code

When creating the files, name them **exactly** as follows so imports work correctly:

| File to Create | Import Name in Other Files |
|---|---|
| `llm/config_llm.py` | `from config_llm import ...` |
| `llm/serialise_deal.py` | `from serialise_deal import serialise_deal` |
| `llm/rag_predict.py` | `from rag_predict import predict_single` |
| `llm/01_build_vector_store.py` | run directly |
| `llm/02_serialise_deal.py` | **rename to `serialise_deal.py`** (no number prefix) |
| `llm/03_rag_predict.py` | **rename to `rag_predict.py`** (no number prefix) |
| `llm/04_batch_score_llm.py` | run directly |
| `llm/05_compare_models.py` | run directly |
| `llm/prompts/win_predictor.txt` | read by `rag_predict.py` |

> The numbered files `01_`, `04_`, `05_` are entry points (run directly).
> The files without numbers (`config_llm.py`, `serialise_deal.py`, `rag_predict.py`) are modules (imported by others).

---

## 13. Execution Order for Claude Code

Run these steps in this exact sequence:

```
# Step 1 — Install dependencies
pip install -r llm/requirements_llm.txt

# Step 2 — Install and start Ollama (one-time setup, done manually)
# Download from https://ollama.com
ollama pull llama3.2:3b
ollama serve              # keep this running in a separate terminal

# Step 3 — Build the vector store (runs once, ~2-3 mins)
cd llm
python 01_build_vector_store.py

# Step 4 — Test on a single deal (optional sanity check)
python -c "
import pandas as pd, snowflake.connector
from config_llm import SNOWFLAKE_CONFIG
from serialise_deal import serialise_deal
from rag_predict import predict_single
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
df = pd.read_sql('SELECT * FROM SALES_WIN_DB.ML.ML_DEAL_FEATURES WHERE TARGET IS NULL LIMIT 1', conn)
conn.close()
result = predict_single(df.iloc[0].to_dict())
print(result)
"

# Step 5 — Create output tables in Snowflake (run the CREATE TABLE SQLs from Sections 9 and 10)

# Step 6 — Batch score all open deals (slow — ~30s per deal on CPU)
python 04_batch_score_llm.py

# Step 7 — Build comparison table
python 05_compare_models.py

# Step 8 — Refresh Power BI report (add pages 7 and 8)
```

---

## 14. Guardrails for Claude Code

1. **Do not modify anything in `ml/`** — the XGBoost pipeline is untouched.
2. **Do not modify any dbt models** — the feature table structure is fixed.
3. **All new files go in `llm/`** — no exceptions.
4. **Never hard-code Snowflake credentials** — always use `os.getenv()` via `config_llm.py`.
5. **Snowflake column names are UPPERCASE** — always use `row.get("COLUMN_NAME")` with uppercase keys when reading from Snowflake DataFrames.
6. **The `serialise_deal()` function must use the exact decode maps** in Section 6 — the encoded integer columns must be decoded to human-readable strings for the LLM to reason about them.
7. **`TARGET IS NULL` = open deals** (for scoring). **`TARGET IS NOT NULL` = closed deals** (for vector store). Never confuse these.
8. **ChromaDB is cosine similarity** — make sure `hnsw:space: cosine` is set when creating the collection (see Section 7).
9. **Ollama must be running** before any script that calls `predict_single()`. If Ollama is not running, the script should fail with a clear error message, not a silent hang.
10. **The `temperature` for Ollama must be `0.1` or lower** — higher temperature produces non-parseable or inconsistent probability outputs.
11. **The probability parser must handle both `0.72` and `72` formats** — some LLMs write percentages as whole numbers. The parse function in Section 8 handles this with `raw / 100.0 if raw > 1.0 else raw`.
12. **`llm/chroma_db/` must be in `.gitignore`** — it can be 100MB+ and should not be committed.
```
