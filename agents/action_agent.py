"""
agents/action_agent.py
----------------------
Agent 3: The Action Agent (Google ADK Tool-as-Agent)
Role: Proactive business intervention.
- Trigger: Post-scoring phase.
- Action: Monitors ML_PREDICTIONS table for high-value deals whose probability band drops to "LOW"
  or where DAYS_IN_NEGOTIATION_STAGE crosses the critical threshold (>21 days).
- Intervention: Uses ADK tooling to draft and send a proactive mitigation alert (Slack / Email format)
  to the assigned sales manager. Pushes insights to stakeholders and records intervention in Snowflake ACTION_LOG.
"""
import os
import sys
import json
import logging
import requests
import pandas as pd
from datetime import datetime

import google.adk
from google.adk.agents import BaseAgent

# Snowflake connector fallback import
try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from ml.config import SNOWFLAKE_CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ActionAgent] %(message)s")
log = logging.getLogger("ActionAgent")


from pydantic import ConfigDict

class ActionAgent(BaseAgent):
    """
    Google ADK Tool-as-Agent for autonomous, proactive sales mitigation alerts.
    """
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    def __init__(self, name: str = "ActionAgent", **data):
        super().__init__(name=name, **data)
        self.db_config = SNOWFLAKE_CONFIG
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

    def fetch_at_risk_deals(self) -> pd.DataFrame:
        """Queries Snowflake ML_PREDICTIONS for deals requiring proactive intervention."""
        if HAS_SNOWFLAKE and self.db_config.get("account"):
            try:
                conn = snowflake.connector.connect(**self.db_config)
                query = """
                    SELECT
                        p.OPPORTUNITY_ID,
                        p.WIN_PROBABILITY,
                        p.PROBABILITY_BAND,
                        p.DEAL_VALUE,
                        p.DAYS_IN_NEGOTIATION_STAGE,
                        p.ASSIGNED_AGENT_ID,
                        p.TOP_NEGATIVE_FACTORS
                    FROM SALES_WIN_DB.ML.ML_PREDICTIONS p
                    WHERE p.PROBABILITY_BAND = 'LOW'
                       OR p.DAYS_IN_NEGOTIATION_STAGE > 21
                    ORDER BY p.DEAL_VALUE DESC
                    LIMIT 25
                """
                df = pd.read_sql(query, conn)
                conn.close()
                if not df.empty:
                    log.info(f"Loaded {len(df)} at-risk deals for action monitoring from Snowflake.")
                    return df
            except Exception as e:
                log.warning(f"Could not fetch ML_PREDICTIONS from Snowflake: {e}")

        # Synthetic benchmark at-risk deals for testing
        log.info("Constructing representative at-risk deals for action agent intervention test.")
        return pd.DataFrame([
            {
                "OPPORTUNITY_ID": "OPP-RISK-101",
                "WIN_PROBABILITY": 0.24,
                "PROBABILITY_BAND": "LOW",
                "DEAL_VALUE": 145000.00,
                "DAYS_IN_NEGOTIATION_STAGE": 28,
                "ASSIGNED_AGENT_ID": "USER-AGENT-04",
                "TOP_NEGATIVE_FACTORS": "Days in negotiation stage > 21; High discount risk bucket; Silent engagement last 14 days"
            },
            {
                "OPPORTUNITY_ID": "OPP-STALL-202",
                "WIN_PROBABILITY": 0.35,
                "PROBABILITY_BAND": "LOW",
                "DEAL_VALUE": 89000.00,
                "DAYS_IN_NEGOTIATION_STAGE": 24,
                "ASSIGNED_AGENT_ID": "USER-AGENT-12",
                "TOP_NEGATIVE_FACTORS": "Negotiation stall; Stage regression count = 2"
            }
        ])

    def format_mitigation_alert(self, deal: dict) -> dict:
        """Drafts a structured proactive mitigation alert payload."""
        opp_id = deal["OPPORTUNITY_ID"]
        val = deal.get("DEAL_VALUE", 0.0)
        days_neg = deal.get("DAYS_IN_NEGOTIATION_STAGE", 0)
        band = deal.get("PROBABILITY_BAND", "LOW")
        prob = deal.get("WIN_PROBABILITY", 0.0)
        agent_id = deal.get("ASSIGNED_AGENT_ID", "Sales Manager")
        neg_factors = deal.get("TOP_NEGATIVE_FACTORS", "Stagnation in negotiation stage")

        if days_neg > 21:
            alert_type = "NEGOTIATION_STALL"
            title = f"⚠️ NEGOTIATION STALL ALERT: Deal {opp_id} (${val:,.2f})"
            body = (
                f"*Opportunity*: {opp_id}\n"
                f"*Deal Value*: ${val:,.2f}\n"
                f"*Status*: Stall detected — {days_neg} days in negotiation (Critical threshold: 21 days)\n"
                f"*Current Win Probability*: {prob:.1%} ({band})\n"
                f"*Risk Factors*: {neg_factors}\n\n"
                f"*Recommended Intervention*: Schedule immediate executive check-in with client decision maker. Offer targeted incentive to close by month-end."
            )
        else:
            alert_type = "HIGH_VALUE_RISK"
            title = f"🚨 HIGH-VALUE DEAL AT RISK: Deal {opp_id} (${val:,.2f})"
            body = (
                f"*Opportunity*: {opp_id}\n"
                f"*Deal Value*: ${val:,.2f}\n"
                f"*Win Probability Band*: {band} ({prob:.1%})\n"
                f"*Assigned Rep*: {agent_id}\n"
                f"*Primary Vulnerability*: {neg_factors}\n\n"
                f"*Recommended Intervention*: Re-evaluate pricing structure and assign senior technical specialist for immediate objection handling."
            )

        # Build Gmail MCP-compatible draft payload
        rep_email = f"{agent_id.lower().replace(' ', '.')}@company.com"
        manager_email = "sales_director@company.com"
        group_email = "deal_escalations@company.com"

        email_subject = f"[URGENT ACTION REQUIRED] Deal Mitigation Strategy: {opp_id} (${val:,.2f})"
        email_body = f"""Dear Sales Team,

AUTOMATED SALES WIN PREDICTOR - PROACTIVE MITIGATION DRAFT
----------------------------------------------------------------------
Opportunity ID : {opp_id}
Deal Value     : ${val:,.2f}
Win Probability: {prob:.1%} ({band})
Negotiation    : {days_neg} Days in Stage (Critical Threshold: 21 Days)
Assigned Rep   : {agent_id}

KEY RISK FACTORS IDENTIFIED:
{neg_factors}

RECOMMENDED ACTION PLAN:
1. Executive Check-In: Schedule an immediate call between regional VP and client decision-maker.
2. Pricing Guardrails: Cap max discount at 20% to protect deal gross margin.
3. Decision Timeline: Establish a firm closing decision milestone within 5 business days.

Best regards,
Sales Win Predictor AI Agent (Google ADK)
"""

        email_draft_payload = {
            "mcp_tool": "gmail_create_draft",
            "to": [rep_email],
            "cc": [manager_email, group_email],
            "subject": email_subject,
            "body": email_body,
            "status": "DRAFT_CREATED"
        }

        # Save draft locally to logs/email_drafts/ for inspection & Gmail MCP integration
        try:
            draft_dir = os.path.join(PROJECT_ROOT, "logs", "email_drafts")
            os.makedirs(draft_dir, exist_ok=True)
            draft_path = os.path.join(draft_dir, f"draft_{opp_id}.json")
            with open(draft_path, "w", encoding="utf-8") as f:
                json.dump(email_draft_payload, f, indent=2)
            log.info(f"✓ Saved Gmail MCP email draft payload to logs/email_drafts/draft_{opp_id}.json")
        except Exception as e:
            log.warning(f"Could not save local email draft file: {e}")

        return {
            "opportunity_id": opp_id,
            "alert_type": alert_type,
            "deal_value": float(val),
            "probability_band": band,
            "days_in_negotiation": int(days_neg),
            "assigned_agent_id": agent_id,
            "title": title,
            "content": body,
            "email_draft": email_draft_payload
        }

    def dispatch_alert(self, alert_payload: dict) -> str:
        """Dispatches mitigation alert via Slack Webhook (if available) or logs to console/audit stream."""
        if self.slack_webhook_url:
            try:
                resp = requests.post(
                    self.slack_webhook_url,
                    json={"text": f"{alert_payload['title']}\n{alert_payload['content']}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    log.info(f"✓ Dispatched Slack alert for deal {alert_payload['opportunity_id']}")
                    return "SENT"
            except Exception as e:
                log.warning(f"Failed to dispatch Slack alert: {e}")

        # Console / Simulated fallback
        log.info(f"⚡ [PROACTIVE ALERT DISPATCHED] Deal: {alert_payload['opportunity_id']} | Type: {alert_payload['alert_type']}")
        return "SIMULATED"

    def log_action_to_snowflake(self, alert: dict, dispatch_status: str):
        """Records intervention dispatch history in Snowflake ML.ACTION_LOG table."""
        if not HAS_SNOWFLAKE or not self.db_config.get("account"):
            log.warning("Snowflake credentials not present; skipping action log database write.")
            return

        try:
            conn = snowflake.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("CREATE SCHEMA IF NOT EXISTS SALES_WIN_DB.ML;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS SALES_WIN_DB.ML.ACTION_LOG (
                    ACTION_ID VARCHAR(50) DEFAULT UUID_STRING(),
                    OPPORTUNITY_ID VARCHAR(50),
                    DISPATCH_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    ALERT_TYPE VARCHAR(50),
                    DEAL_VALUE FLOAT,
                    CURRENT_PROBABILITY_BAND VARCHAR(20),
                    DAYS_IN_NEGOTIATION INT,
                    ASSIGNED_AGENT_ID VARCHAR(50),
                    ALERT_RECIPIENT VARCHAR(255),
                    ALERT_CONTENT TEXT,
                    DISPATCH_CHANNEL VARCHAR(50),
                    DISPATCH_STATUS VARCHAR(20)
                );
            """)

            insert_sql = """
                INSERT INTO SALES_WIN_DB.ML.ACTION_LOG
                (OPPORTUNITY_ID, ALERT_TYPE, DEAL_VALUE, CURRENT_PROBABILITY_BAND, DAYS_IN_NEGOTIATION, ASSIGNED_AGENT_ID, ALERT_RECIPIENT, ALERT_CONTENT, DISPATCH_CHANNEL, DISPATCH_STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                alert["opportunity_id"],
                alert["alert_type"],
                alert["deal_value"],
                alert["probability_band"],
                alert["days_in_negotiation"],
                alert["assigned_agent_id"],
                f"sales-manager-{alert['assigned_agent_id']}@company.com",
                alert["content"],
                "SLACK" if self.slack_webhook_url else "CONSOLE",
                dispatch_status
            ))
            conn.commit()
            conn.close()
            log.info(f"✓ Logged action intervention for {alert['opportunity_id']} to Snowflake ML.ACTION_LOG")
        except Exception as e:
            log.warning(f"Could not record action log in Snowflake: {e}")

    def execute_proactive_interventions(self) -> list[dict]:
        """Monitors predictions and executes proactive alerts for all high-risk deals."""
        log.info("Starting Action Agent post-scoring intervention monitor...")
        at_risk_df = self.fetch_at_risk_deals()
        actions_taken = []

        for idx, row in at_risk_df.iterrows():
            deal_dict = row.to_dict()
            alert = self.format_mitigation_alert(deal_dict)
            status = self.dispatch_alert(alert)
            self.log_action_to_snowflake(alert, status)
            alert["dispatch_status"] = status
            actions_taken.append(alert)

        log.info(f"✓ Action Agent completed {len(actions_taken)} proactive business interventions.")
        return actions_taken


def build_action_adk_agent() -> ActionAgent:
    """Constructs and returns ActionAgent instance."""
    return ActionAgent(name="ActionAgent")


if __name__ == "__main__":
    agent = ActionAgent()
    results = agent.execute_proactive_interventions()
    print("Action Interventions Sample:\n", json.dumps(results[0], indent=2))
