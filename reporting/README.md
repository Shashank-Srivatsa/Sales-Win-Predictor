# 📊 Reporting: Power BI Dashboards

Create interactive Power BI dashboards from Snowflake data to visualize deal insights, predictions, and pipeline health.

---

## 📋 Overview

This layer:
- Connects Power BI to Snowflake
- Creates data models
- Builds executive dashboards
- Visualizes predictions and insights
- Enables self-service analytics

**Output**: Interactive Power BI reports for sales leadership

---

## ✅ Prerequisites

- ✅ Power BI Desktop installed ([download](https://powerbi.microsoft.com/desktop/))
- ✅ Snowflake data loaded with dbt models and LLM insights
- ✅ Snowflake credentials and connection details

---

## 🛠️ Step 1: Connect Power BI to Snowflake

### 1.1 Install Snowflake Connector

```
In Power BI Desktop:
1. File → Options and settings → Options
2. Security → Set Privacy Level if needed
3. Get Data → Snowflake (Database)
```

### 1.2 Create Connection

```
In Power BI:
1. Home → Get Data → Snowflake
2. Enter:
   - Server: xy12345-ab67890.snowflakecomputing.com
   - Warehouse: COMPUTE_WH
   - Database: sales_win_predictor
3. Click OK
```

### 1.3 Load Tables

Select these tables to import:
```
- dbt_prod.fct_opportunities
- dbt_prod.dim_accounts
- dbt_prod.dim_users
- dbt_prod.llm_opportunity_insights
- features.pred_opportunity_predictions
```

---

## 📐 Step 2: Create Data Model

### 2.1 Set Up Relationships

In Power BI Model view:

```
Relationships to create:
1. fct_opportunities.opportunity_id 
   ↔ pred_opportunity_predictions.opportunity_id

2. fct_opportunities.account_id 
   ↔ dim_accounts.account_id

3. fct_opportunities.owner_user_id 
   ↔ dim_users.user_id

4. fct_opportunities.opportunity_id 
   ↔ llm_opportunity_insights.opportunity_id
```

### 2.2 Create Calculated Columns

In Power BI:

**Win Probability Category**:
```
Win_Probability_Category = 
IF([win_probability] > 0.7, "High",
   IF([win_probability] > 0.4, "Medium", "Low"))
```

**Deal Size Category**:
```
Deal_Size = 
IF([amount] > 100000, "Enterprise",
   IF([amount] > 50000, "Large",
      IF([amount] > 10000, "Medium", "Small")))
```

**Days in Stage**:
```
Days_In_Stage = DATEDIFF([created_date], TODAY(), DAY)
```

---

## 📊 Step 3: Build Executive Dashboard

### 3.1 Overview Page

**Visualizations**:

1. **KPI Cards** (4 cards across top):
   - Total Pipeline: `SUM(amount)` - Format: $M
   - Win Rate: `SUM(is_won)/COUNT(*)` - Format: %
   - Avg Deal Size: `AVERAGE(amount)` - Format: $K
   - Expected Revenue (weighted): `SUMPRODUCT(amount, win_probability)` - Format: $M

2. **Stage Waterfall**:
   - X-axis: `stage`
   - Y-axis: `SUM(amount)`
   - Sorted by stage progression

3. **Win Probability Distribution**:
   - Histogram of `win_probability`
   - Show count of opportunities by probability bucket

4. **Pipeline by Account**:
   - Bar chart: Account Name vs Amount
   - Top 10 accounts
   - Color by `Win_Probability_Category`

---

### 3.2 Deal Details Page

**Visualizations**:

1. **Opportunities Table**:
   ```
   Columns:
   - Opportunity Name
   - Account
   - Stage
   - Amount
   - Win Probability
   - Days Open
   - Owner
   ```
   Sort by: Amount (descending)

2. **Deal Trend Line**:
   - X-axis: Created Date (by Month)
   - Y-axis: COUNT(opportunity_id)
   - Show Won vs Open

3. **Rep Performance Matrix**:
   - X-axis: `rep_win_rate`
   - Y-axis: `COUNT(deals)`
   - Size: `SUM(amount)`
   - Legend: Region

4. **Stage Distribution Pie**:
   - Slices: Stage
   - Size: Count of opportunities

---

### 3.3 Insights Page

**Visualizations**:

1. **LLM Insights Text Box**:
   ```
   Add a text box showing latest insights:
   (Click on deal in table to show insight)
   ```

2. **Key Risks**:
   - Table filtering for `win_probability < 0.4`
   - Sort by: Amount (descending)
   - Show: Name, Amount, Risk Factors

3. **High-Probability Deals**:
   - Table of deals with `win_probability > 0.7`
   - Show: Name, Amount, Days Open, Next Action

4. **Activity Summary**:
   - Donut chart: Activity Type distribution
   - Filter by Stage

---

## 📁 Step 4: Publish Reports

### 4.1 Publish to Power BI Service

```
In Power BI Desktop:
1. File → Publish
2. Select workspace
3. Click Select
4. Wait for publication
```

### 4.2 Set Up Refresh Schedule

```
In Power BI Service:
1. Dataset → Scheduled Refresh
2. Set Frequency: Daily
3. Time: 3:00 AM (after dbt run at 2 AM)
4. Notifications: Email on failure
```

---

## 🔄 Step 5: Create DirectQuery (Optional - Better Performance)

Instead of importing data, use DirectQuery to always query live Snowflake:

```
In Power BI:
1. Home → Transform Data → Query Editor
2. Select each query
3. Right-click → Delete (import mode)
4. Home → Get Data → Snowflake (DirectQuery)
```

**Pros**: Always fresh data, lower storage
**Cons**: May be slower, needs Snowflake gateway

---

## 📈 Step 6: Set Up Row-Level Security (Optional)

Allow sales reps to see only their deals:

```
In Power BI Service:
1. Model tab
2. Manage roles
3. Create role "Sales Rep"
4. Add filter: [owner_user_id] = USERNAME()
5. Save
6. Test role
```

---

## 🎨 Step 7: Design Best Practices

### Color Scheme
```
Green: High probability (>0.7)
Yellow: Medium probability (0.4-0.7)
Red: Low probability (<0.4)
```

### Drill-through
Create drill-through from:
- Account → Account details page
- Deal → Deal deep-dive
- Rep → Rep performance

### Bookmarks
Create bookmarks for:
- High-value deals view
- At-risk deals view
- New opportunities
- Closed won

---

## 📊 Sample DAX Measures

Add these to your data model:

```dax
-- Total Pipeline
Total_Pipeline = SUM('fct_opportunities'[amount])

-- Weighted Expected Revenue
Weighted_Revenue = SUMPRODUCT(
    'fct_opportunities'[amount],
    'pred_opportunity_predictions'[win_probability]
)

-- Win Rate %
Win_Rate = 
DIVIDE(
    COUNTIF('fct_opportunities'[is_won], 1),
    COUNTA('fct_opportunities'[opportunity_id]),
    0
)

-- Opportunities by Rep
Rep_Deal_Count = CALCULATE(
    COUNTA('fct_opportunities'[opportunity_id]),
    GROUPBY('dim_users'[user_id])
)

-- Average Days Open
Avg_Days_Open = AVERAGE('fct_opportunities'[days_open])
```

---

## 🔧 Step 8: Automate Updates

### 8.1 Create Refresh Script

```bash
#!/bin/bash
# reporting/refresh_powerbi.sh

# Run dbt to update tables
cd /path/to/Sales-Win-Predictor
dbt run --target prod

# Refresh Power BI dataset (requires Power BI REST API)
curl -X POST \
  https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes \
  -H "Authorization: Bearer $POWERBI_TOKEN" \
  -H "Content-Type: application/json"

echo "✓ Power BI refresh triggered"
```

### 8.2 Schedule with Cron

```bash
# Run daily at 2:30 AM (after dbt at 2:00 AM)
30 2 * * * bash /path/to/reporting/refresh_powerbi.sh >> refresh.log 2>&1
```

---

## 📱 Step 9: Mobile View

Configure Power BI reports for mobile:

```
View → Mobile Layout
1. Drag key visuals to mobile canvas
2. Remove less critical charts
3. Stack vertically
4. Large touch targets
```

---

## 📈 Sample Reports Structure

```
Sales Win Predictor
├── Executive Dashboard
│   ├── KPIs (4 cards)
│   ├── Pipeline by stage
│   ├── Probability distribution
│   └── Top accounts
│
├── Deal Analysis
│   ├── Opportunities table (sortable/filterable)
│   ├── Win probability scatter
│   ├── Deal trends by time
│   └── Activity levels
│
├── Rep Performance
│   ├── Deals by rep
│   ├── Win rate comparison
│   ├── Revenue attribution
│   └── Pipeline coverage
│
├── Insights & Recommendations
│   ├── High-risk deals
│   ├── High-probability opportunities
│   ├── LLM-generated insights
│   └── Next action recommendations
│
└── Pipeline Health
    ├── Stage distribution
    ├── Sales velocity
    ├── Forecast accuracy
    └── Win rate by stage
```

---

## 🚀 Deployment Checklist

- [ ] All Snowflake tables loaded and verified
- [ ] dbt models running successfully
- [ ] Power BI connected to Snowflake
- [ ] Data model relationships created
- [ ] All visualizations working
- [ ] Calculated columns/measures added
- [ ] Refresh schedule configured
- [ ] Reports published to workspace
- [ ] Stakeholders have access
- [ ] Mobile layout optimized

---

## 📊 Query Examples for Custom Visuals

### High-Value At-Risk Deals
```sql
SELECT TOP 10
    opportunity_name,
    account_name,
    amount,
    win_probability,
    days_open
FROM dbt_prod.fct_opportunities
WHERE is_open = 1
  AND amount > 50000
  AND win_probability < 0.4
ORDER BY amount DESC
```

### Win Rate by Industry
```sql
SELECT
    industry,
    COUNT(*) as total_deals,
    SUM(CASE WHEN is_won = 1 THEN 1 ELSE 0 END) as won,
    100.0 * SUM(CASE WHEN is_won = 1 THEN 1 ELSE 0 END) / COUNT(*) as win_rate_pct
FROM dbt_prod.fct_opportunities
GROUP BY industry
ORDER BY win_rate_pct DESC
```

---

## 🐛 Troubleshooting

### "Connection failed to Snowflake"
- Verify credentials
- Check Snowflake warehouse is running
- Ensure IP is whitelisted (if applicable)

### "Data not refreshing"
- Check refresh schedule in Power BI Service
- Verify dbt is completing successfully
- Check Snowflake query logs

### "Slow performance"
- Use DirectQuery for large datasets
- Create aggregation tables
- Add indexes in Snowflake
- Reduce number of visuals per page

---

## 🚀 Next Steps

- Share reports with stakeholders
- Gather feedback on visualizations
- Add filters for different roles
- Set up email subscriptions
- Create mobile-optimized views

---

## 📚 Resources

- [Power BI Documentation](https://docs.microsoft.com/en-us/power-bi/)
- [Snowflake Power BI Connector](https://docs.snowflake.com/en/user-guide/power-bi-connector.html)
- [DAX Function Reference](https://dax.guide/)
- [Power BI Design Best Practices](https://www.microsoft.com/en-us/microsoft-365/business/microsoft-power-bi)
