"""
rag_predict.py
--------------
Given one deal (as a dict from ML_DEAL_FEATURES), returns:
  - llm_win_probability (float 0.0-1.0)
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
        tpl_path = os.path.join(os.path.dirname(__file__), "prompts", "win_predictor.txt")
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


def _parse_response(response_text: str) -> tuple:
    """
    Extract probability and reasoning from the LLM response.
    Returns (probability, reasoning). Defaults to 0.5 if parsing fails.
    """
    probability = 0.5
    reasoning   = response_text.strip()

    prob_match = re.search(
        r"PROBABILITY:\s*([0-9]+\.?[0-9]*)",
        response_text, re.IGNORECASE
    )
    if prob_match:
        raw = float(prob_match.group(1))
        # Handle if model writes 72 instead of 0.72
        probability = raw / 100.0 if raw > 1.0 else raw
        probability = max(0.01, min(0.99, probability))

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
        llm_win_probability : float (0.0-1.0)
        llm_probability_band: str  (HIGH / MEDIUM / LOW)
        llm_reasoning       : str
        similar_deals_count : int
        similar_deal_ids    : str  (comma-separated)
        llm_model_used      : str
    """
    _load_resources()

    opp_id    = str(deal_row.get("OPPORTUNITY_ID", "UNKNOWN"))
    deal_text = serialise_deal(deal_row)

    # ── Step 1: Embed the new deal ───────────────────────────────────────────
    query_embedding = _embedder.encode(deal_text).tolist()

    # ── Step 2: Retrieve top K similar historical deals ──────────────────────
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K_SIMILAR_DEALS,
        include=["documents", "metadatas", "distances"],
    )
    similar_docs  = results["documents"][0]
    similar_metas = results["metadatas"][0]
    similar_ids   = [m["opportunity_id"] for m in similar_metas]

    # ── Step 3: Build the prompt ─────────────────────────────────────────────
    examples_block = _build_examples_block(similar_docs, similar_metas)
    prompt = _prompt_tpl.format(
        n_examples=TOP_K_SIMILAR_DEALS,
        examples_block=examples_block,
        new_deal_text=deal_text,
    )

    # ── Step 4: Call Ollama (local LLM) ──────────────────────────────────────
    try:
        client   = ollama.Client(host=OLLAMA_HOST)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "temperature": 0.1,
                "num_predict": 200,
                "stop": ["\n\n\n"],
            },
        )
    except Exception as e:
        raise RuntimeError(
            f"Ollama is not reachable at {OLLAMA_HOST}. "
            f"Start it with: ollama serve\nOriginal error: {e}"
        ) from e

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
        "llm_reasoning":        reasoning[:1000],
        "similar_deals_count":  len(similar_ids),
        "similar_deal_ids":     ",".join(similar_ids[:5]),
        "llm_model_used":       OLLAMA_MODEL,
        "raw_llm_response":     response_text[:500],
    }
