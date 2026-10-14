"""
dags/sales_win_predictor_dag.py
--------------------------------
Apache Airflow DAG for Sales Win Predictor Multi-Agent Pipeline.

Orchestrates:
1. FileSensor / Stage Trigger
2. Agent 1: Pipeline Watcher (dbt run & test + self-healing)
3. Quantitative ML Scoring (XGBoost + SHAP)
4. Qualitative LLM RAG Scoring (ChromaDB + Ollama)
5. Model Convergence & Discrepancy Flagging
6. Agent 2: Deal Strategist (Strategic Brief Generation)
7. Agent 3: Action Agent (Proactive Business Interventions & Alerts)
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Path setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

default_args = {
    'owner': 'sales_win_predictor',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sales_win_predictor_multi_agent_pipeline',
    default_args=default_args,
    description='End-to-End Autonomous Multi-Agent Sales Win Predictor DAG',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # Task 1: Pipeline Watcher (Agent 1 - Data Cleaning & Self-Healing)
    task_pipeline_watcher = BashOperator(
        task_id='agent_1_pipeline_watcher',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "agents", "pipeline_watcher.py")}"',
    )

    # Task 2: Quantitative ML Deal Scoring (XGBoost)
    task_ml_scoring = BashOperator(
        task_id='stage_2_ml_scoring',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "ml", "05_score.py")}" && python "{os.path.join(PROJECT_ROOT, "ml", "06_write_predictions.py")}"',
    )

    # Task 3: Qualitative LLM RAG Deal Scoring
    task_llm_scoring = BashOperator(
        task_id='stage_3_llm_rag_scoring',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "llm", "04_batch_score_llm.py")}"',
    )

    # Task 4: Model Discrepancy Convergence Engine
    task_compare_models = BashOperator(
        task_id='stage_4_compare_models',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "llm", "05_compare_models.py")}"',
    )

    # Task 5: Deal Strategist (Agent 2 - Strategic Briefs for Flagged Deals)
    task_deal_strategist = BashOperator(
        task_id='agent_2_deal_strategist',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "agents", "deal_strategist.py")}"',
    )

    # Task 6: Action Agent (Agent 3 - Proactive Mitigation Alerts)
    task_action_agent = BashOperator(
        task_id='agent_3_action_agent',
        bash_command=f'python "{os.path.join(PROJECT_ROOT, "agents", "action_agent.py")}"',
    )

    # DAG Dependency Workflow Topology
    task_pipeline_watcher >> [task_ml_scoring, task_llm_scoring] >> task_compare_models
    task_compare_models >> task_deal_strategist >> task_action_agent
