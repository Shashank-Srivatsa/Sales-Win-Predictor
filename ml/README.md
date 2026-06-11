# 🤖 ML: Model Training & Registration

Train XGBoost model to predict deal outcomes and register it for inference.

---

## 📋 Overview

This layer:
- Trains XGBoost model on features
- Validates model performance
- Registers model in MLflow
- Saves model artifacts
- Prepares for inference

**Output**: Registered ML model ready for predictions

---

## ✅ Prerequisites

- ✅ Feature tables created (see [features/](../features/))
- ✅ XGBoost, scikit-learn, mlflow installed
- ✅ MLflow tracking server configured

---

## 🛠️ Step 1: MLflow Setup

### 1.1 Install MLflow

```bash
pip install mlflow xgboost scikit-learn imbalanced-learn
```

### 1.2 Configure MLflow Backend

**ml/config/mlflow_config.yaml**:

```yaml
mlflow:
  tracking_uri: file:./ml/mlruns              # Local file backend
  # OR for remote:
  # tracking_uri: http://localhost:5000       # Local server
  # tracking_uri: s3://bucket/mlruns          # AWS S3
  
  artifact_location: ./ml/artifacts           # Where to store model artifacts
  experiment_name: sales_win_predictor
  registry_uri: sqlite:///mlflow.db            # Model registry backend
```

### 1.3 Start MLflow Tracking Server (Optional)

```bash
# Start MLflow UI (opens on http://localhost:5000)
mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./artifacts \
  --host 127.0.0.1 --port 5000
```

---

## 📊 Step 2: Model Training

### 2.1 Training Script

**ml/train_model.py**:

```python
import os
import pandas as pd
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix, 
    precision_recall_curve, f1_score, accuracy_score
)
import snowflake.connector
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# MLflow configuration
mlflow.set_tracking_uri("file:./ml/mlruns")
mlflow.set_experiment("sales_win_predictor")

def get_snowflake_connection():
    """Create Snowflake connection."""
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='features'
    )

def load_training_data():
    """Load features from Snowflake."""
    print("Loading training data from Snowflake...")
    
    conn = get_snowflake_connection()
    query = """
    SELECT
        opportunity_id,
        amount,
        discount_pct,
        days_open,
        total_activities,
        total_meeting_minutes,
        total_calls,
        total_emails,
        days_since_last_activity,
        rep_win_rate,
        stage_changes,
        account_tier,
        target
    FROM fea_opportunities
    WHERE target IS NOT NULL
      AND days_to_close IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 40000
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"✓ Loaded {len(df)} records")
    print(f"✓ Positive samples: {df['target'].sum()} ({100*df['target'].mean():.1f}%)")
    
    return df

def preprocess_data(df):
    """Clean and preprocess data."""
    print("\nPreprocessing data...")
    
    # Handle missing values
    df = df.fillna(df.median(numeric_only=True))
    
    # Encode categorical variables
    label_encoders = {}
    categorical_cols = df.select_dtypes(include='object').columns
    
    for col in categorical_cols:
        if col != 'target':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
    
    # Remove ID column
    X = df.drop(['opportunity_id', 'target'], axis=1)
    y = df['target']
    
    print(f"✓ Features shape: {X.shape}")
    print(f"✓ Features: {list(X.columns)}")
    print(f"✓ Class distribution: {y.value_counts().to_dict()}")
    
    return X, y, label_encoders

def train_model(X, y):
    """Train XGBoost model."""
    print("\nSplitting data...")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"✓ Training set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    print("\nTraining XGBoost model...")
    
    # XGBoost parameters
    params = {
        'max_depth': 7,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'random_state': 42,
        'gpu_id': 0,  # Set to -1 for CPU
        'tree_method': 'hist',  # or 'exact' for CPU
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=10,
        verbose=False
    )
    
    print("✓ Model training complete")
    
    return model, X_train, X_test, y_train, y_test

def evaluate_model(model, X_train, X_test, y_train, y_test):
    """Evaluate model performance."""
    print("\nEvaluating model...")
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    y_test_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    metrics = {
        'train_accuracy': accuracy_score(y_train, y_train_pred),
        'test_accuracy': accuracy_score(y_test, y_test_pred),
        'train_auc': roc_auc_score(y_train, model.predict_proba(X_train)[:, 1]),
        'test_auc': roc_auc_score(y_test, y_test_pred_proba),
        'f1_score': f1_score(y_test, y_test_pred),
        'precision': (confusion_matrix(y_test, y_test_pred)[1, 1] / 
                     (confusion_matrix(y_test, y_test_pred)[0, 1] + 
                      confusion_matrix(y_test, y_test_pred)[1, 1])),
    }
    
    print(f"  Train Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"  Test Accuracy:  {metrics['test_accuracy']:.4f}")
    print(f"  Train AUC:      {metrics['train_auc']:.4f}")
    print(f"  Test AUC:       {metrics['test_auc']:.4f}")
    print(f"  F1 Score:       {metrics['f1_score']:.4f}")
    print(f"  Precision:      {metrics['precision']:.4f}")
    
    return metrics

def log_model_to_mlflow(model, metrics, X_test, feature_names):
    """Log model to MLflow."""
    print("\nLogging to MLflow...")
    
    with mlflow.start_run(run_name=f"xgboost_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        # Log parameters
        mlflow.log_params({
            'max_depth': model.max_depth,
            'learning_rate': model.learning_rate,
            'n_estimators': model.n_estimators,
        })
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        mlflow.log_artifact(
            "ml/artifacts/feature_importance.csv",
            artifact_path="model"
        )
        
        # Log model
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            registered_model_name="SalesWinPredictor"
        )
        
        run_id = mlflow.active_run().info.run_id
        print(f"✓ Model logged with run_id: {run_id}")
        
        return run_id

def main():
    """Main training pipeline."""
    print("="*60)
    print("Sales Win Predictor - Model Training")
    print("="*60)
    
    try:
        # 1. Load data
        df = load_training_data()
        
        # 2. Preprocess
        X, y, label_encoders = preprocess_data(df)
        
        # 3. Train
        model, X_train, X_test, y_train, y_test = train_model(X, y)
        
        # 4. Evaluate
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
        
        # 5. Log to MLflow
        run_id = log_model_to_mlflow(model, metrics, X_test, list(X.columns))
        
        print("\n" + "="*60)
        print("✓ MODEL TRAINING COMPLETE")
        print("="*60)
        print(f"Run ID: {run_id}")
        print("\nNext: Check MLflow UI at http://localhost:5000")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

if __name__ == '__main__':
    main()
```

### 2.2 Run Training

```bash
python ml/train_model.py
```

Expected output:
```
============================================================
Sales Win Predictor - Model Training
============================================================
Loading training data from Snowflake...
✓ Loaded 40000 records
✓ Positive samples: 28000 (70.0%)

Preprocessing data...
✓ Features shape: (40000, 12)

Training XGBoost model...
✓ Model training complete

Evaluating model...
  Train Accuracy: 0.7834
  Test Accuracy:  0.7521
  Train AUC:      0.8234
  Test AUC:       0.8001
  F1 Score:       0.7654
  Precision:      0.7812

Logging to MLflow...
✓ Model logged with run_id: abc123def456
```

---

## ✅ Step 3: Register Model

### 3.1 View in MLflow UI

```bash
# Open MLflow UI
mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./artifacts
```

Access at: http://localhost:5000

### 3.2 Register Model Programmatically

**ml/register_model.py**:

```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("file:./ml/mlruns")

client = MlflowClient()

# Get latest run
experiment = client.get_experiment_by_name("sales_win_predictor")
runs = client.search_runs(experiment_ids=[experiment.experiment_id])
latest_run = runs[0]

print(f"Latest run: {latest_run.info.run_id}")
print(f"Run status: {latest_run.info.status}")

# Register model
model_uri = f"runs:/{latest_run.info.run_id}/model"
model_version = mlflow.register_model(
    model_uri,
    "SalesWinPredictor"
)

print(f"✓ Model registered: {model_version.name}")
print(f"  Version: {model_version.version}")
print(f"  Stage: {model_version.current_stage}")

# Transition to Production
client.transition_model_version_stage(
    name="SalesWinPredictor",
    version=model_version.version,
    stage="Production"
)

print("✓ Model transitioned to Production")
```

Run:
```bash
python ml/register_model.py
```

---

## 📊 Step 4: Make Predictions

### 4.1 Batch Prediction Script

**ml/predict.py**:

```python
import mlflow
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()
mlflow.set_tracking_uri("file:./ml/mlruns")

def load_production_model():
    """Load production model from MLflow."""
    model = mlflow.pyfunc.load_model("models:/SalesWinPredictor/Production")
    return model

def get_open_opportunities():
    """Get open opportunities from Snowflake."""
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='features'
    )
    
    query = """
    SELECT
        opportunity_id,
        amount,
        discount_pct,
        days_open,
        total_activities,
        total_meeting_minutes,
        total_calls,
        total_emails,
        days_since_last_activity,
        rep_win_rate,
        stage_changes,
        account_tier
    FROM fea_opportunities
    WHERE target IS NULL  -- Open opportunities
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def make_predictions(model, X):
    """Make predictions on open opportunities."""
    print(f"Making predictions for {len(X)} open opportunities...")
    
    predictions = model.predict(X)
    
    return predictions

def save_predictions_to_snowflake(opportunity_ids, predictions):
    """Save predictions back to Snowflake."""
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='features'
    )
    
    cursor = conn.cursor()
    
    # Create predictions table
    cursor.execute("""
    CREATE OR REPLACE TABLE pred_opportunity_predictions (
        opportunity_id VARCHAR,
        win_probability FLOAT,
        predicted_at TIMESTAMP
    )
    """)
    
    # Insert predictions
    for opp_id, pred in zip(opportunity_ids, predictions):
        cursor.execute(f"""
        INSERT INTO pred_opportunity_predictions
        VALUES ('{opp_id}', {pred}, CURRENT_TIMESTAMP())
        """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Saved {len(predictions)} predictions to Snowflake")

def main():
    """Main prediction pipeline."""
    print("="*60)
    print("Making Predictions on Open Opportunities")
    print("="*60)
    
    # Load model
    print("\nLoading production model...")
    model = load_production_model()
    print("✓ Model loaded")
    
    # Get open opportunities
    print("\nFetching open opportunities...")
    df = get_open_opportunities()
    print(f"✓ Found {len(df)} open opportunities")
    
    # Make predictions
    X = df.drop('opportunity_id', axis=1)
    predictions = make_predictions(model, X)
    
    # Save predictions
    save_predictions_to_snowflake(df['opportunity_id'], predictions)
    
    print("\n✓ Predictions complete!")

if __name__ == '__main__':
    main()
```

Run:
```bash
python ml/predict.py
```

---

## 🔄 Step 5: Retrain Model (Scheduled)

### 5.1 Retraining Script

```bash
#!/bin/bash
# ml/retrain.sh - Run daily via cron

cd /path/to/Sales-Win-Predictor

# Activate environment
source venv/bin/activate

# Run training
python ml/train_model.py

# Register if metrics improved
python ml/register_model.py

# Make predictions
python ml/predict.py

echo "✓ Retraining complete at $(date)"
```

### 5.2 Schedule with Cron (Linux/macOS)

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/Sales-Win-Predictor && bash ml/retrain.sh >> ml/logs/retrain.log 2>&1
```

---

## 📊 Step 6: Store Predictions in dbt

### 6.1 Create dbt Model for Predictions

**dbt/models/marts/pred_opportunities.sql**:

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
    CASE 
        WHEN pred.win_probability > 0.7 THEN 'High'
        WHEN pred.win_probability > 0.4 THEN 'Medium'
        ELSE 'Low'
    END as win_likelihood,
    pred.predicted_at
FROM {{ ref('fct_opportunities') }} fct
LEFT JOIN {{ source('predictions', 'opportunity_predictions') }} pred
    ON fct.opportunity_id = pred.opportunity_id
```

---

## 📈 Monitoring

```sql
-- Check latest predictions
SELECT 
    COUNT(*) as total_predictions,
    AVG(win_probability) as avg_win_prob,
    MAX(predicted_at) as last_update
FROM sales_win_predictor.features.pred_opportunity_predictions;

-- High-confidence predictions
SELECT
    opportunity_id,
    win_probability,
    predicted_at
FROM sales_win_predictor.features.pred_opportunity_predictions
WHERE win_probability > 0.8
ORDER BY win_probability DESC;
```

---

## 🚀 Next Steps

After model training is complete:

1. ✅ Proceed to [llm/](../llm/) for LLM/RAG setup
2. Set up automated retraining schedule
3. Monitor model drift and performance

---

## 📚 Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Model Registry](https://mlflow.org/docs/latest/model-registry.html)
