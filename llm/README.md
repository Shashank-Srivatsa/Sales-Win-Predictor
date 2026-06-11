# 🧠 LLM + RAG: AI-Powered Insights Layer

Add LLM intelligence with Retrieval-Augmented Generation (RAG) to generate deal insights, recommendations, and contextual analysis.

---

## 📋 Overview

This layer:
- Embeds CRM data into vector store (ChromaDB)
- Retrieves relevant context for each deal
- Queries Claude API for intelligent insights
- Generates actionable recommendations
- Stores results back in Snowflake

**Output**: AI-generated deal insights, risk summaries, and action items

---

## ✅ Prerequisites

- ✅ ML model trained and predictions created (see [ml/](../ml/))
- ✅ Claude API key (from [console.anthropic.com](https://console.anthropic.com))
- ✅ Python packages: anthropic, chromadb, sentence-transformers

---

## 🛠️ Step 1: Setup

### 1.1 Install Dependencies

```bash
pip install anthropic chromadb sentence-transformers
```

### 1.2 Add Claude API Key

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-v1-xxx...
```

---

## 📚 Step 2: Build Vector Store

### 2.1 Create Vector Database

**llm/build_vector_store.py**:

```python
import os
import chromadb
from chromadb.config import Settings
import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import json

load_dotenv()

def get_snowflake_connection():
    """Create Snowflake connection."""
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

def load_deal_documents():
    """Load deal data from Snowflake for embedding."""
    print("Loading deal documents from Snowflake...")
    
    conn = get_snowflake_connection()
    query = """
    SELECT
        opp.opportunity_id,
        opp.opportunity_name,
        opp.account_id,
        acc.account_name,
        acc.industry,
        opp.stage,
        opp.amount,
        opp.discount_pct,
        usr.first_name || ' ' || usr.last_name as owner_name,
        pred.win_probability,
        feat.total_activities,
        feat.days_open
    FROM sales_win_predictor.dbt_dev.fct_opportunities opp
    LEFT JOIN sales_win_predictor.dbt_dev.dim_accounts acc
        ON opp.account_id = acc.account_id
    LEFT JOIN sales_win_predictor.dbt_dev.dim_users usr
        ON opp.owner_user_id = usr.user_id
    LEFT JOIN sales_win_predictor.features.fea_opportunities feat
        ON opp.opportunity_id = feat.opportunity_id
    LEFT JOIN sales_win_predictor.features.pred_opportunity_predictions pred
        ON opp.opportunity_id = pred.opportunity_id
    LIMIT 1000
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Create text documents for embedding
    documents = []
    metadatas = []
    ids = []
    
    for _, row in df.iterrows():
        doc = f"""
        Deal: {row['opportunity_name']}
        Account: {row['account_name']} ({row['industry']})
        Amount: ${row['amount']:,.0f}
        Stage: {row['stage']}
        Owner: {row['owner_name']}
        Win Probability: {row['win_probability']:.2%}
        Activities: {row['total_activities']}
        Days Open: {row['days_open']}
        
        Summary: {row['opportunity_name']} is a {row['stage'].lower()} opportunity 
        with {row['account_name']} valued at ${row['amount']:,.0f}. 
        The deal has {row['total_activities']} recorded activities and has been 
        open for {row['days_open']} days. Current prediction score is {row['win_probability']:.1%}.
        """
        
        documents.append(doc)
        metadatas.append({
            'opportunity_id': str(row['opportunity_id']),
            'account_name': str(row['account_name']),
            'amount': float(row['amount']),
            'stage': str(row['stage']),
            'win_probability': float(row['win_probability']),
        })
        ids.append(str(row['opportunity_id']))
    
    print(f"✓ Loaded {len(documents)} documents")
    return documents, metadatas, ids

def build_vector_store():
    """Build ChromaDB vector store."""
    print("\nBuilding vector store...")
    
    # Initialize ChromaDB
    chroma_db_dir = './llm/chroma_db'
    os.makedirs(chroma_db_dir, exist_ok=True)
    
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb",
            persist_directory=chroma_db_dir,
            anonymized_telemetry=False
        )
    )
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="sales_opportunities",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Load documents
    documents, metadatas, ids = load_deal_documents()
    
    # Add to collection
    print("Adding documents to collection...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    # Persist
    client.persist()
    
    print(f"✓ Vector store created with {len(documents)} documents")
    print(f"  Location: {chroma_db_dir}")
    
    return client, collection

def verify_store(collection):
    """Verify vector store with sample query."""
    print("\nVerifying vector store...")
    
    test_query = "high value deals in technology sector"
    results = collection.query(
        query_texts=[test_query],
        n_results=3
    )
    
    print(f"✓ Sample query: '{test_query}'")
    print(f"  Results found: {len(results['ids'][0])}")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc[:100]}...")

def main():
    print("="*60)
    print("Building Vector Store for RAG")
    print("="*60)
    
    try:
        client, collection = build_vector_store()
        verify_store(collection)
        print("\n✓ Vector store ready for LLM queries!")
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

if __name__ == '__main__':
    main()
```

Run:
```bash
python llm/build_vector_store.py
```

---

## 🤖 Step 3: Query with Claude LLM

### 3.1 RAG Query Script

**llm/rag_query.py**:

```python
import os
import chromadb
from chromadb.config import Settings
from anthropic import Anthropic
from dotenv import load_dotenv
import json

load_dotenv()

def load_vector_store():
    """Load ChromaDB vector store."""
    chroma_db_dir = './llm/chroma_db'
    
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb",
            persist_directory=chroma_db_dir,
            anonymized_telemetry=False
        )
    )
    
    collection = client.get_collection("sales_opportunities")
    return collection

def retrieve_context(collection, query, n_results=3):
    """Retrieve relevant documents from vector store."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    context_docs = "\n".join(results['documents'][0])
    return context_docs

def query_claude_with_rag(query, context):
    """Query Claude with RAG context."""
    client = Anthropic()
    
    system_prompt = """You are a sales intelligence assistant. 
    You analyze CRM data and provide actionable insights for sales teams.
    
    Your responses should:
    1. Be data-driven and specific
    2. Provide clear recommendations
    3. Highlight risks and opportunities
    4. Suggest next actions
    5. Use the provided deal context to support your analysis"""
    
    user_message = f"""
    Based on this CRM data:
    
    {context}
    
    Please answer: {query}
    
    Provide specific, actionable insights."""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    return response.content[0].text

def main():
    print("="*60)
    print("RAG Query Engine - Sales Intelligence")
    print("="*60)
    
    # Load vector store
    print("\nLoading vector store...")
    collection = load_vector_store()
    print("✓ Vector store loaded")
    
    # Example queries
    queries = [
        "What are the key risks in large enterprise deals?",
        "Which accounts have the most engagement activities?",
        "Summarize the status of technology sector opportunities",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        # Retrieve context
        context = retrieve_context(collection, query, n_results=5)
        
        # Query Claude
        response = query_claude_with_rag(query, context)
        
        print(f"\nResponse:\n{response}")

if __name__ == '__main__':
    main()
```

Run:
```bash
python llm/rag_query.py
```

---

## 📊 Step 4: Generate Deal Insights

### 4.1 Automated Insight Generation

**llm/generate_insights.py**:

```python
import os
import chromadb
from chromadb.config import Settings
import snowflake.connector
from anthropic import Anthropic
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def load_vector_store():
    """Load ChromaDB vector store."""
    chroma_db_dir = './llm/chroma_db'
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb",
            persist_directory=chroma_db_dir,
            anonymized_telemetry=False
        )
    )
    return client.get_collection("sales_opportunities")

def get_open_opportunities():
    """Get high-priority open opportunities."""
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )
    
    query = """
    SELECT
        opp.opportunity_id,
        opp.opportunity_name,
        acc.account_name,
        opp.amount,
        opp.stage,
        pred.win_probability
    FROM sales_win_predictor.dbt_dev.fct_opportunities opp
    LEFT JOIN sales_win_predictor.dbt_dev.dim_accounts acc
        ON opp.account_id = acc.account_id
    LEFT JOIN sales_win_predictor.features.pred_opportunity_predictions pred
        ON opp.opportunity_id = pred.opportunity_id
    WHERE opp.is_open = 1
      AND opp.amount > 50000
    ORDER BY opp.amount DESC
    LIMIT 10  -- Top 10 opportunities
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def generate_deal_summary(collection, opportunity_id, opportunity_name, account_name, amount, stage, win_prob):
    """Generate LLM summary for a single deal."""
    
    # Retrieve relevant context
    query_text = f"Deal {opportunity_name} at {account_name}"
    results = collection.query(
        query_texts=[query_text],
        n_results=5
    )
    
    context = results['documents'][0][0] if results['documents'][0] else ""
    
    # Generate insight
    client = Anthropic()
    
    prompt = f"""
    Analyze this sales opportunity and provide a concise executive summary:
    
    Deal: {opportunity_name}
    Account: {account_name}
    Amount: ${amount:,.0f}
    Current Stage: {stage}
    Win Probability (AI): {win_prob:.1%}
    
    Context: {context}
    
    Provide in 150 words:
    1. Deal Status: Current situation
    2. Key Risks: What could go wrong
    3. Next Actions: Recommended steps
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def save_insights_to_snowflake(insights_df):
    """Save insights back to Snowflake."""
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='features'
    )
    
    cursor = conn.cursor()
    
    # Create insights table
    cursor.execute("""
    CREATE OR REPLACE TABLE llm_deal_insights (
        opportunity_id VARCHAR,
        insight_text VARCHAR,
        generated_at TIMESTAMP
    )
    """)
    
    # Insert insights
    for _, row in insights_df.iterrows():
        cursor.execute(f"""
        INSERT INTO llm_deal_insights
        VALUES ('{row['opportunity_id']}', ?, CURRENT_TIMESTAMP())
        """, (row['insight'],))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Saved {len(insights_df)} insights to Snowflake")

def main():
    print("="*60)
    print("Generating Deal Insights with LLM+RAG")
    print("="*60)
    
    # Load vector store
    print("\nLoading vector store...")
    collection = load_vector_store()
    
    # Get open opportunities
    print("Fetching high-priority opportunities...")
    opportunities = get_open_opportunities()
    print(f"✓ Found {len(opportunities)} opportunities")
    
    # Generate insights
    print("\nGenerating LLM insights...")
    insights_list = []
    
    for idx, row in opportunities.iterrows():
        print(f"  [{idx+1}/{len(opportunities)}] {row['opportunity_name']}...", end=" ")
        
        insight = generate_deal_summary(
            collection,
            row['opportunity_id'],
            row['opportunity_name'],
            row['account_name'],
            row['amount'],
            row['stage'],
            row['win_probability']
        )
        
        insights_list.append({
            'opportunity_id': row['opportunity_id'],
            'insight': insight
        })
        
        print("✓")
    
    # Save to Snowflake
    insights_df = pd.DataFrame(insights_list)
    save_insights_to_snowflake(insights_df)
    
    print("\n✓ Insight generation complete!")

if __name__ == '__main__':
    main()
```

Run:
```bash
python llm/generate_insights.py
```

---

## 🔄 Step 5: Integrate with dbt

### 5.1 Create dbt Model for Insights

**dbt/models/marts/llm_opportunity_insights.sql**:

```sql
{{ config(
    materialized='table',
    schema='dbt_prod'
) }}

SELECT
    fct.opportunity_id,
    fct.opportunity_name,
    fct.account_id,
    fct.stage,
    fct.amount,
    pred.win_probability,
    llm.insight_text,
    llm.generated_at as insight_generated_at
FROM {{ ref('fct_opportunities') }} fct
LEFT JOIN {{ source('features', 'pred_opportunity_predictions') }} pred
    ON fct.opportunity_id = pred.opportunity_id
LEFT JOIN {{ source('features', 'llm_deal_insights') }} llm
    ON fct.opportunity_id = llm.opportunity_id
ORDER BY fct.amount DESC
```

### 5.2 Run dbt with LLM Results

```bash
# Run dbt to materialize insights
dbt run --select llm_opportunity_insights
```

---

## 📈 Step 6: Pipeline Orchestration

### 6.1 Master Pipeline Script

**llm/run_full_pipeline.py**:

```python
import subprocess
import os
from datetime import datetime

def run_command(command, description):
    """Run shell command and report status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print('='*60)
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode == 0:
        print(f"✓ {description} complete")
    else:
        print(f"✗ {description} failed")
        raise Exception(f"Command failed: {command}")

def main():
    print("="*60)
    print(f"FULL LLM+RAG PIPELINE - {datetime.now()}")
    print("="*60)
    
    try:
        # 1. Build vector store
        run_command(
            "python llm/build_vector_store.py",
            "Building Vector Store"
        )
        
        # 2. Generate insights
        run_command(
            "python llm/generate_insights.py",
            "Generating Deal Insights"
        )
        
        # 3. Run dbt
        run_command(
            "dbt run --select llm_opportunity_insights",
            "Running dbt Materialization"
        )
        
        print("\n" + "="*60)
        print("✓ FULL PIPELINE COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()
```

Run:
```bash
python llm/run_full_pipeline.py
```

---

## 🚀 Next Steps

After LLM/RAG layer is set up:

1. ✅ Proceed to [reporting/](../reporting/) to create Power BI reports
2. Set up scheduled pipeline runs
3. Monitor LLM costs and performance

---

## 📚 Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Retrieval-Augmented Generation](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)
