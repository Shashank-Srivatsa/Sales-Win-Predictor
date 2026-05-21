DIVISION_MAP  = {0: "TalentEdge", 1: "CreativeMotion", 2: "PulseMedia", 3: "BrandVault"}
REGION_MAP    = {0: "North America", 1: "Europe", 2: "India", 3: "Asia Pacific", 4: "Australia"}
DEAL_TYPE_MAP = {0: "New Business", 1: "Renewal", 2: "Upsell", 3: "Cross-sell"}
SENIORITY_MAP = {1: "Junior", 2: "Mid-level", 3: "Senior", 4: "Director", 5: "VP/Head"}
TIER_MAP      = {1: "Tier 1 (top client)", 2: "Tier 2 (mid-tier)", 3: "Tier 3 (small/new)"}


def serialise_deal(row: dict) -> str:
    """
    Convert one deal's feature row into a natural language description.
    row: a dictionary of {column_name: value} for one deal.
    Returns: a multi-line string describing the deal in business language.
    """
    division  = DIVISION_MAP.get(int(row.get("DIVISION_ENCODED", 0)), "Unknown")
    region    = REGION_MAP.get(int(row.get("REGION_ENCODED", 0)), "Unknown")
    deal_type = DEAL_TYPE_MAP.get(int(row.get("DEAL_TYPE_ENCODED", 0)), "New Business")
    seniority = SENIORITY_MAP.get(int(row.get("AGENT_SENIORITY_LEVEL", 2)), "Mid-level")
    tier      = TIER_MAP.get(int(row.get("ACCOUNT_TIER", 3)), "Tier 3 (small/new)")

    discount   = float(row.get("DISCOUNT_PCT", 0))
    disc_signal = (
        "well below the safe threshold — strong pricing"  if discount < 10 else
        "within the acceptable range"                     if discount < 20 else
        "above the 20% warning level"                     if discount < 30 else
        "critically high — historically predicts loss"
    )

    velocity    = float(row.get("DEAL_VELOCITY_SCORE", 1.0))
    vel_signal  = (
        "moving faster than average — positive momentum"       if velocity > 1.1 else
        "moving at average pace"                               if velocity > 0.8 else
        "moving slower than average — risk of stalling"        if velocity > 0.5 else
        "critically slow — significantly behind average pace"
    )

    agent_wr    = float(row.get("AGENT_TRAILING_12M_WIN_RATE", 0.4))
    agent_signal = (
        "excellent (above 50%)"   if agent_wr > 0.50 else
        "above average (40-50%)"  if agent_wr > 0.40 else
        "below average (30-40%)"  if agent_wr > 0.30 else
        "poor (below 30%)"
    )

    days_neg   = float(row.get("DAYS_IN_NEGOTIATION_STAGE", 0))
    neg_signal = (
        "fast negotiation — positive"       if days_neg < 10 else
        "normal negotiation pace"           if days_neg < 21 else
        "negotiation is running long"       if days_neg < 35 else
        "negotiation is critically stalled"
    )

    engagement  = float(row.get("ENGAGEMENT_SCORE", 0.5))
    eng_signal  = (
        "client is highly engaged recently"                       if engagement > 0.6 else
        "client engagement is moderate"                           if engagement > 0.3 else
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
