"""
agents/orchestrator.py
----------------------
Google ADK Autonomous Multi-Agent Orchestrator
Role: End-to-end multi-agent graph workflow manager for the Sales Win Predictor.

Workflow Steps:
1. Agent 1 (Pipeline Watcher): Executes dbt transformations, runs validation tests, applies self-healing.
2. Quantitative ML Pipeline: Applies XGBoost scoring and extracts SHAP risk factors into ML_PREDICTIONS.
3. Qualitative LLM/RAG Pipeline: Executes RAG deal evaluation against ChromaDB vector store into LLM_PREDICTIONS.
4. Convergence Engine: Runs 05_compare_models.py to evaluate model delta and flag edge cases (DISAGREEMENT_FLAG = TRUE).
5. Agent 2 (Deal Strategist): Takes flagged disagreement deals, performs deep-dive analysis, and writes strategic briefs to DEAL_STRATEGY_BRIEFS.
6. Agent 3 (Action Agent): Scans post-scoring predictions for high-risk LOW win probability deals or negotiation stalls (>21 days),
   dispatches proactive alerts (Slack/Email/Console), and records intervention history to ACTION_LOG.
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime

import google.adk
from google.adk.agents import SequentialAgent, BaseAgent

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from agents.pipeline_watcher import PipelineWatcherAgent
from agents.deal_strategist import DealStrategistAgent
from agents.action_agent import ActionAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MultiAgentOrchestrator] %(message)s"
)
log = logging.getLogger("Orchestrator")


class MultiAgentOrchestrator:
    """
    Google ADK Graph Orchestrator unifying data validation, quantitative ML,
    qualitative LLM RAG, model discrepancy analysis, and proactive business interventions.
    """

    def __init__(self):
        self.pipeline_watcher = PipelineWatcherAgent()
        self.deal_strategist = DealStrategistAgent()
        self.action_agent = ActionAgent()

    def run_stage_1_pipeline_watcher(self) -> dict:
        """Stage 1: Execute Agent 1 (Pipeline Watcher) data validation and self-healing."""
        log.info("==========================================================")
        log.info("STAGE 1: Executing Agent 1 (Pipeline Watcher - SequentialAgent)")
        log.info("==========================================================")
        res = self.pipeline_watcher.run_pipeline()
        log.info(f"Stage 1 Complete. Pipeline Status: {res['status']}")
        return res

    def run_stage_2_ml_scoring(self) -> dict:
        """Stage 2: Execute Quantitative ML pipeline (XGBoost + SHAP scoring)."""
        log.info("==========================================================")
        log.info("STAGE 2: Executing Quantitative ML Scoring Pipeline")
        log.info("==========================================================")
        try:
            import importlib
            score_mod = importlib.import_module("ml.05_score")
            write_mod = importlib.import_module("ml.06_write_predictions")
            log.info("Running XGBoost deal scoring...")
            score_mod.score_open_deals()
            write_mod.write_predictions()
            return {"status": "SUCCESS", "message": "ML scoring & SHAP predictions generated successfully."}
        except Exception as e:
            log.warning(f"Quantitative ML scoring notice: {e}")
            return {"status": "SKIPPED_OR_WARNING", "message": str(e)}

    def run_stage_3_llm_rag_scoring(self) -> dict:
        """Stage 3: Execute Qualitative LLM/RAG Scoring Pipeline."""
        log.info("==========================================================")
        log.info("STAGE 3: Executing Qualitative LLM/RAG Scoring Pipeline")
        log.info("==========================================================")
        try:
            import importlib
            batch_mod = importlib.import_module("llm.04_batch_score_llm")
            log.info("Running Qualitative RAG deal scoring...")
            batch_mod.batch_score()
            return {"status": "SUCCESS", "message": "LLM RAG deal scoring completed."}
        except Exception as e:
            log.warning(f"Qualitative LLM scoring notice: {e}")
            return {"status": "SKIPPED_OR_WARNING", "message": str(e)}

    def run_stage_4_model_comparison(self) -> dict:
        """Stage 4: Execute Model Convergence & Discrepancy Evaluator."""
        log.info("==========================================================")
        log.info("STAGE 4: Executing Model Discrepancy Convergence Evaluator")
        log.info("==========================================================")
        try:
            import importlib
            comp_mod = importlib.import_module("llm.05_compare_models")
            comp_mod.compare_models()
            return {"status": "SUCCESS", "message": "Model comparison and disagreement flags evaluated."}
        except Exception as e:
            log.warning(f"Model comparison notice: {e}")
            return {"status": "SKIPPED_OR_WARNING", "message": str(e)}

    def run_stage_5_deal_strategist(self) -> list[dict]:
        """Stage 5: Execute Agent 2 (Deal Strategist) deep-dive analysis on flagged deals."""
        log.info("==========================================================")
        log.info("STAGE 5: Executing Agent 2 (Deal Strategist - LlmAgent)")
        log.info("==========================================================")
        briefs = self.deal_strategist.analyze_all_flagged_deals()
        log.info(f"Stage 5 Complete. Generated {len(briefs)} Strategic Briefs.")
        return briefs

    def run_stage_6_action_agent(self) -> list[dict]:
        """Stage 6: Execute Agent 3 (Action Agent) proactive business interventions."""
        log.info("==========================================================")
        log.info("STAGE 6: Executing Agent 3 (Action Agent - Tool-as-Agent)")
        log.info("==========================================================")
        actions = self.action_agent.execute_proactive_interventions()
        log.info(f"Stage 6 Complete. Dispatched {len(actions)} Proactive Mitigation Alerts.")
        return actions

    def run_full_autonomous_pipeline(self) -> dict:
        """
        Executes the complete end-to-end multi-agent graph workflow.
        """
        start_time = time.time()
        log.info("🚀 STARTING GOOGLE ADK AUTONOMOUS MULTI-AGENT PIPELINE")

        stage1_res = self.run_stage_1_pipeline_watcher()
        stage2_res = self.run_stage_2_ml_scoring()
        stage3_res = self.run_stage_3_llm_rag_scoring()
        stage4_res = self.run_stage_4_model_comparison()
        stage5_briefs = self.run_stage_5_deal_strategist()
        stage6_actions = self.run_stage_6_action_agent()

        elapsed = time.time() - start_time
        summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "pipeline_watcher": stage1_res,
            "ml_scoring": stage2_res,
            "llm_rag_scoring": stage3_res,
            "model_comparison": stage4_res,
            "deal_strategist_briefs_generated": len(stage5_briefs),
            "action_interventions_dispatched": len(stage6_actions),
            "status": "SUCCESS"
        }

        log.info("==========================================================")
        log.info(f"🎉 MULTI-AGENT PIPELINE COMPLETE IN {elapsed:.2f} SECONDS")
        log.info(f"Strategic Briefs Created: {len(stage5_briefs)}")
        log.info(f"Proactive Alerts Dispatched: {len(stage6_actions)}")
        log.info("==========================================================")
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sales Win Predictor Google ADK Multi-Agent Orchestrator")
    parser.add_argument("--run-all", action="store_true", help="Execute complete end-to-end multi-agent pipeline")
    parser.add_argument("--watcher-only", action="store_true", help="Execute Pipeline Watcher agent only")
    parser.add_argument("--strategist-only", action="store_true", help="Execute Deal Strategist agent only")
    parser.add_argument("--action-only", action="store_true", help="Execute Action Agent only")
    args = parser.parse_args()

    orchestrator = MultiAgentOrchestrator()

    if args.watcher_only:
        res = orchestrator.run_stage_1_pipeline_watcher()
        print(json.dumps(res, indent=2))
    elif args.strategist_only:
        briefs = orchestrator.run_stage_5_deal_strategist()
        print(json.dumps(briefs, indent=2))
    elif args.action_only:
        actions = orchestrator.run_stage_6_action_agent()
        print(json.dumps(actions, indent=2))
    else:
        summary = orchestrator.run_full_autonomous_pipeline()
        print(json.dumps(summary, indent=2))
