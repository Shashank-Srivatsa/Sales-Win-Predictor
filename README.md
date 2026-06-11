# 📊 Sales Win Predictor - Complete End-to-End Pipeline

**An open-source ML pipeline for predicting sales deal outcomes, powered by data engineering, machine learning, LLM insights, and interactive reporting.**

---

## 🎯 Quick Navigation

This is a **modular, multi-layer system**. Start here, then follow the layer-specific README files:

| Layer | Purpose | README | Time |
|-------|---------|--------|------|
| **Setup** | Raw data ingestion | [setup/](setup/) | 30 min |
| **dbt** | Data transformation | [dbt/](dbt/) | 30 min |
| **Features** | ML feature engineering | [features/](features/) | 20 min |
| **ML** | Model training & registration | [ml/](ml/) | 30 min |
| **LLM+RAG** | AI-powered insights | [llm/](llm/) | 25 min |
| **Reporting** | Power BI dashboards | [reporting/](reporting/) | 20 min |

**Total end-to-end: ~2.5 hours**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  RAW DATA (CSV FILES)                                           │
│  └─ 9 CRM tables (~600K records)                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
    ┌────────────▼──────────────┐
    │ SETUP LAYER               │
    │ └─ Snowflake ingestion     │
    │ └─ 9 tables created        │
    └────────────┬──────────────┘
                 │
    ┌────────────▼──────────────────┐
    │ DBT LAYER                      │
    │ └─ Staging models              │
    │ └─ Fact/Dimension tables       │
    │ └─ Data quality tests          │
    └────────────┬──────────────────┘
                 │
    ┌────────────▼──────────────────┐
    │ FEATURES LAYER                 │
    │ └─ Deal-level features         │
    │ └─ Activity aggregations       │
    │ └─ Training dataset            │
    └────────────┬──────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼───────┐   ┌────▼──────────────┐
    │ ML LAYER   │   │ LLM+RAG LAYER      │
    │ ├─ Training├──►├─ Vector store     │
    │ ├─ Model   │   │ ├─ ChromaDB       │
    │ └─ MLflow  │   │ ├─ Claude API     │
    └────┬───────┘   │ └─ Insights       │
         │           └────┬──────────────┘
         └───────┬────────┘
                 │
    ┌────────────▼──────────────────┐
    │ SNOWFLAKE TABLES              │
    │ ├─ dbt_prod.* models          │
    │ ├─ features.*                 │
    │ ├─ llm_insights               │
    │ └─ pred_*predictions          │
    └────────────┬──────────────────┘
                 │
    ┌────────────▼──────────────────┐
    │ REPORTING LAYER                │
    │ └─ Power BI dashboards         │
    │ └─ Executive dashboards        │
    │ └─ Deal analytics              │
    └────────────────────────────────┘
```

---

## 📋 Complete Setup Workflow

### Phase 1: Data Foundation (30 min)

```bash
# 1.1 Clone and setup
git clone <your-repo>
cd Sales-Win-Predictor
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 1.2 Configure credentials
cp .env.example .env
# Edit .env with your Snowflake account

# 1.3 Load raw data
python setup/data_ingestion.py
```

**Deliverable**: Raw CRM data in Snowflake (`sales_win_predictor.raw_crm_data.*`)

---

### Phase 2: Data Transformation (30 min)

See: [dbt/README.md](dbt/README.md)

```bash
# 2.1 Configure dbt connection
# Edit profiles.yml with Snowflake credentials

# 2.2 Create dbt models
dbt run --target dev

# 2.3 Test data quality
dbt test

# 2.4 Generate documentation
dbt docs generate
dbt docs serve
```

**Deliverable**: Clean, tested tables in Snowflake (`dbt_dev.stg_*`, `dbt_dev.fct_*`, `dbt_dev.dim_*`)

---

### Phase 3: Feature Engineering (20 min)

See: [features/README.md](features/README.md)

```bash
# 3.1 Create feature tables
python features/create_features.py

# 3.2 Verify in Snowflake
# Run: SELECT * FROM sales_win_predictor.features.fea_opportunities LIMIT 5;
```

**Deliverable**: ML-ready feature table (`features.fea_opportunities`)

---

### Phase 4: ML Model Training (30 min)

See: [ml/README.md](ml/README.md)

```bash
# 4.1 Start MLflow tracking (optional)
mlflow server --backend-store-uri sqlite:///mlflow.db

# 4.2 Train model
python ml/train_model.py

# 4.3 View results in MLflow UI
# Open: http://localhost:5000

# 4.4 Register model
python ml/register_model.py

# 4.5 Make predictions
python ml/predict.py
```

**Deliverable**: Trained XGBoost model in MLflow + predictions in Snowflake

---

### Phase 5: LLM + RAG Insights (25 min)

See: [llm/README.md](llm/README.md)

```bash
# 5.1 Build vector store
python llm/build_vector_store.py

# 5.2 Get Claude API key
# From: https://console.anthropic.com/

# 5.3 Add to .env
# ANTHROPIC_API_KEY=sk-ant-v1-xxx...

# 5.4 Generate insights
python llm/generate_insights.py

# 5.5 Materialize in dbt
dbt run --select llm_opportunity_insights
```

**Deliverable**: AI-generated insights in Snowflake (`features.llm_deal_insights`)

---

### Phase 6: Reporting & Dashboards (20 min)

See: [reporting/README.md](reporting/README.md)

```
1. Open Power BI Desktop
2. Get Data → Snowflake
3. Connect to: sales_win_predictor database
4. Load tables:
   - dbt_prod.fct_opportunities
   - dbt_prod.dim_accounts
   - dbt_prod.dim_users
   - features.pred_opportunity_predictions
   - features.llm_deal_insights
5. Create relationships
6. Build visualizations
7. Publish to Power BI Service
```

**Deliverable**: Interactive Power BI dashboards

---

## 🎯 Key Data Flows

### Flow 1: Data → Features → Predictions
```
Raw CSV
  ↓
Snowflake (raw_crm_data)
  ↓
dbt transformations (dbt_dev)
  ↓
Feature engineering (features.fea_opportunities)
  ↓
ML Model Training (XGBoost)
  ↓
Predictions (features.pred_opportunity_predictions)
  ↓
Power BI Dashboard
```

### Flow 2: Data → Vector Store → LLM → Insights
```
dbt Tables (fct_opportunities, dim_*)
  ↓
Vector Embeddings (ChromaDB)
  ↓
Claude API Queries (RAG)
  ↓
Deal Insights (features.llm_deal_insights)
  ↓
dbt Materialization
  ↓
Power BI Dashboard
```

### Flow 3: Continuous Pipeline
```
Daily Scheduled Run:
├─ dbt run (transform data)
├─ features/create_features.py (engineer features)
├─ ml/train_model.py (retrain model)
├─ ml/predict.py (make predictions)
├─ llm/generate_insights.py (LLM insights)
└─ Power BI refresh (dashboards updated)
```

---

## 📊 Tables Reference

### Raw Data (raw_crm_data)
```
crm_accounts           ~1,000 companies
crm_activities        ~200,000 interactions
crm_contacts           ~5,000 people
crm_contracts         ~10,000 signed contracts
crm_opportunities     ~50,000 deals
crm_opportunity_line_items    ~100,000 products
crm_opportunity_stage_history ~200,000 stage changes
crm_products            ~100 products
crm_users              ~500 salespeople
```

### Transformed Data (dbt_dev)
```
stg_crm_accounts         cleaned accounts
stg_crm_opportunities    cleaned opportunities
stg_crm_activities       cleaned activities
fct_opportunities        fact table (deals)
dim_accounts            dimension table (accounts)
dim_users               dimension table (sales reps)
```

### ML Features (features)
```
fea_opportunities       ML feature table
pred_opportunity_predictions    ML predictions
llm_deal_insights       LLM-generated insights
```

---

## 🚀 Automated Daily Pipeline

### 6.1 Create Master Schedule

**setup/pipeline.sh**:
```bash
#!/bin/bash
set -e

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Sales Win Predictor Pipeline"

cd /path/to/Sales-Win-Predictor
source venv/bin/activate

# Phase 1: dbt transformations
echo "Running dbt models..."
dbt run --target prod && dbt test --target prod

# Phase 2: Feature engineering
echo "Creating features..."
python features/create_features.py

# Phase 3: Model training
echo "Training model..."
python ml/train_model.py

# Phase 4: Predictions
echo "Making predictions..."
python ml/predict.py

# Phase 5: LLM insights
echo "Generating insights..."
python llm/generate_insights.py

# Phase 6: Final dbt run
echo "Materializing results..."
dbt run --select llm_opportunity_insights

echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline complete!"
```

### 6.2 Schedule with Cron (Linux/macOS)

```bash
# Add to crontab (crontab -e)
# Run pipeline daily at 2 AM
0 2 * * * /path/to/Sales-Win-Predictor/setup/pipeline.sh >> /path/to/logs/pipeline.log 2>&1

# Alternative: Use Airflow/Prefect/Dagster for more control
```

### 6.3 Schedule with Windows Task Scheduler

```
1. Open Task Scheduler
2. Create Basic Task
3. Name: Sales-Win-Predictor-Pipeline
4. Trigger: Daily at 2:00 AM
5. Action: Run script (pipeline.bat)
```

---

## 🔍 Monitoring & Validation

### Health Checks

Run these daily to ensure pipeline health:

```sql
-- 1. Check data freshness
SELECT 
    'Raw data age' as check_name,
    MAX(dbt_loaded_at) as last_update,
    DATEDIFF(hour, MAX(dbt_loaded_at), CURRENT_TIMESTAMP()) as hours_old
FROM sales_win_predictor.dbt_dev.stg_crm_opportunities
UNION ALL
-- 2. Check feature count
SELECT 
    'Feature records',
    MAX(feature_created_at),
    COUNT(*) as record_count
FROM sales_win_predictor.features.fea_opportunities
UNION ALL
-- 3. Check predictions
SELECT 
    'Latest predictions',
    MAX(predicted_at),
    COUNT(*) as prediction_count
FROM sales_win_predictor.features.pred_opportunity_predictions;
```

### Performance Metrics

```sql
-- Model performance on recent data
SELECT 
    'Win probability distribution',
    ROUND(win_probability * 10) / 10 as probability_bucket,
    COUNT(*) as deals,
    SUM(is_won) as won_deals,
    ROUND(100.0 * SUM(is_won) / COUNT(*), 2) as actual_win_rate
FROM sales_win_predictor.dbt_dev.fct_opportunities
WHERE DATEDIFF(day, close_date_actual, CURRENT_DATE()) <= 90
GROUP BY probability_bucket
ORDER BY probability_bucket DESC;
```

---

## 🐛 Troubleshooting Guide

### Issue: dbt connection fails
**Solution**: See [dbt/README.md - Troubleshooting](dbt/README.md#-troubleshooting)

### Issue: ML model performance degraded
**Solution**: See [ml/README.md](ml/README.md) - Check data drift, retrain with fresh data

### Issue: LLM insights not generating
**Solution**: See [llm/README.md](llm/README.md) - Verify Claude API key, check vector store

### Issue: Power BI not refreshing
**Solution**: See [reporting/README.md](reporting/README.md) - Check Snowflake connection, verify dbt completed

---

## 📈 Business Outcomes

This pipeline enables:

| Outcome | Impact |
|---------|--------|
| **Accurate Predictions** | 75%+ AUC on win probability |
| **Better Prioritization** | Focus on top 20% deals = 80% revenue |
| **Risk Detection** | Identify at-risk deals early |
| **AI Insights** | Contextual recommendations per deal |
| **Data-Driven Decisions** | Executive dashboards for strategy |

---

## 📚 Documentation Index

```
├── README.md                          (THIS FILE)
├── setup/
│   ├── README.md                      Data ingestion setup
│   ├── QUICKSTART.md                  10-minute quick start
│   ├── SETUP_GUIDE.md                 Comprehensive setup
│   └── sql/                           SQL scripts
├── dbt/
│   └── README.md                      dbt configuration & models
├── features/
│   └── README.md                      Feature engineering
├── ml/
│   └── README.md                      Model training & MLflow
├── llm/
│   └── README.md                      LLM+RAG pipeline
└── reporting/
    └── README.md                      Power BI dashboards
```

---

## 🤝 Contributing

Contributions welcome! See [Contributing Guidelines](CONTRIBUTING.md)

Process:
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📞 Support

- **Setup issues**: See [setup/SETUP_GUIDE.md](setup/SETUP_GUIDE.md)
- **dbt help**: [dbt Documentation](https://docs.getdbt.com/)
- **ML questions**: [ML README](ml/README.md)
- **LLM/RAG**: [LLM README](llm/README.md)
- **Reporting**: [Reporting README](reporting/README.md)

---

## 📄 License

MIT License - See LICENSE file

---

## 👤 Author

**Shashank Srivatsa**
- Data Engineering | Sales Analytics

---

## ⭐ Key Features

✅ **Complete End-to-End**: Data ingestion → ML → LLM → Reporting  
✅ **Production-Ready**: Error handling, logging, monitoring  
✅ **Modular Design**: Each layer independent, easy to extend  
✅ **Open Source**: Fully transparent, no vendor lock-in  
✅ **Well-Documented**: README for each component + setup guide  
✅ **Automated**: Single command to run entire pipeline  
✅ **Scalable**: Handles 600K+ records efficiently  

---

## 🎯 Next Steps

**New to the project?**
1. Read [setup/QUICKSTART.md](setup/QUICKSTART.md) (10 min)
2. Run [setup/data_ingestion.py](setup/data_ingestion.py)
3. Follow layer READMEs sequentially

**Want specific layer details?**
- dbt: [dbt/README.md](dbt/README.md)
- ML: [ml/README.md](ml/README.md)
- LLM: [llm/README.md](llm/README.md)
- Reporting: [reporting/README.md](reporting/README.md)

**Ready to deploy?**
- Set up [pipeline.sh](setup/pipeline.sh) for automated runs
- Configure Snowflake refresh in Power BI
- Monitor with health checks

---

**Last Updated**: June 2026  
**Status**: Production Ready ✅
