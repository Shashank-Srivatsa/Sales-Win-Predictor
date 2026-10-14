"""
run_demo.py
-----------
Interactive Live Demo Script for Sales Win Predictor Autonomous Multi-Agent Pipeline.
Runs all 3 Google ADK Agents step-by-step with clean output for audience presentations.
"""
import os
import sys
import time
import json

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from agents.orchestrator import MultiAgentOrchestrator

def print_header(title):
    print("\n" + "=" * 70)
    print(f" DEMO STAGE: {title}")
    print("=" * 70)

def main():
    print("======================================================================")
    print(" SALES WIN PREDICTOR - GOOGLE ADK MULTI-AGENT LIVE DEMO")
    print("======================================================================")
    print(" This demo showcases 3 Autonomous AI Agents managing data quality,")
    print(" model discrepancy resolution, and proactive business interventions.\n")

    orchestrator = MultiAgentOrchestrator()

    # Stage 1: Pipeline Watcher
    print_header("1. Agent 1 - The Pipeline Watcher (Data Self-Healing)")
    res1 = orchestrator.run_stage_1_pipeline_watcher()
    print(f" -> Status: {res1['status']} | Tests Passed: {res1['tests_passed']} | Self-Healing: {res1['summary']}")
    time.sleep(1)

    # Stage 2 & 3: Model Scoring
    print_header("2. Quantitative ML & Qualitative RAG LLM Scoring")
    res2 = orchestrator.run_stage_2_ml_scoring()
    res3 = orchestrator.run_stage_3_llm_rag_scoring()
    print(f" -> Quantitative XGBoost: {res2['status']}")
    print(f" -> Qualitative RAG LLM: {res3['status']}")
    time.sleep(1)

    # Stage 4 & 5: Deal Strategist
    print_header("3. Agent 2 - The Deal Strategist (Discrepancy Briefs)")
    orchestrator.run_stage_4_model_comparison()
    briefs = orchestrator.run_stage_5_deal_strategist()
    if briefs:
        sample = briefs[0]
        print(f"\n [STRATEGIC BRIEF GENERATED FOR {sample['OPPORTUNITY_ID']}]")
        print(f"    - XGBoost Probability: {sample['XGB_WIN_PROBABILITY']:.0%}")
        print(f"    - RAG LLM Probability: {sample['LLM_WIN_PROBABILITY']:.0%}")
        print(f"    - Disagreement Cause:  {sample['DISAGREEMENT_REASON']}")
        print(f"    - Strategic Guidance:  {sample['RECOMMENDED_STRATEGY']}\n")
    time.sleep(1)

    # Stage 6: Action Agent
    print_header("4. Agent 3 - The Action Agent (Proactive Alerts)")
    actions = orchestrator.run_stage_6_action_agent()
    if actions:
        sample_act = actions[0]
        print(f"\n [PROACTIVE ALERT DISPATCHED]")
        print(f"    - Opportunity: {sample_act['opportunity_id']} (${sample_act['deal_value']:,.2f})")
        print(f"    - Alert Type:  {sample_act['alert_type']}")
        print(f"    - Action Text: {sample_act['title']}\n")

    print("======================================================================")
    print(" DEMO COMPLETE: Multi-Agent System Executed Successfully!")
    print("======================================================================")

if __name__ == "__main__":
    main()
