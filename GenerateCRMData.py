"""
=============================================================================
SALES WIN PREDICTOR — Synthetic CRM Dataset Generator
=============================================================================
Project   : Sales Win Predictor
Author    : Solo Data Engineer
Version   : 1.0

WHAT THIS SCRIPT GENERATES
---------------------------
9 CSV files that mimic the raw backend tables of an enterprise CRM
(similar to Salesforce). The data covers 10 years (2015–2024) across
4 business divisions: TalentEdge, CreativeMotion, PulseMedia, BrandVault.

OUTPUT FILES
------------
01. crm_accounts.csv           - Client companies (brands like Nike, Adidas)
02. crm_contacts.csv           - People at those companies (CMOs, buyers)
03. crm_users.csv              - Internal agents and employees
04. crm_opportunities.csv      - The deals (MAIN TABLE — ~1,800 rows)
05. crm_opportunity_line_items.csv  - Each billable item on a deal
06. crm_opportunity_stage_history.csv  - Every stage transition a deal made
07. crm_activities.csv         - Emails, calls, meetings logged per deal
08. crm_contracts.csv          - Contract records (won deals only)
09. crm_products.csv           - Service & talent product catalogue

IMPORTANT DESIGN PRINCIPLES
----------------------------
1. These are RAW CRM backend tables — flat, operational, no star schema.
2. The win/loss outcome (is_won) is CORRELATED with features so the
   ML model can actually learn meaningful patterns.
3. Realistic imperfections are included: some nulls, occasional outliers,
   duplicate agent entries on a deal, etc.
4. Random seed is fixed (SEED = 42) for full reproducibility.

DEPENDENCIES
------------
pip install pandas numpy faker

HOW TO USE
----------
1. Set OUTPUT_PATH below to your desired local folder.
2. Run:  python generate_crm_data.py
3. Nine CSV files will be created at OUTPUT_PATH.
4. Load them into SQL Server / Snowflake as your Bronze layer.

=============================================================================
"""

import os
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker

# =============================================================================
# CONFIGURATION — Edit these values
# =============================================================================

OUTPUT_PATH = r"C:\Users\shash\OneDrive\Documents\Sales-Win-Predictor"
# Change to any folder on your machine, e.g.:
# OUTPUT_PATH = r"C:\Users\YourName\projects\sales_win_predictor\data\raw"
# OUTPUT_PATH = "/home/yourname/projects/crm_data"

SEED        = 42          # Fixed seed → same data every run
START_YEAR  = 2015        # 10 years of history
END_YEAR    = 2024
N_ACCOUNTS  = 220         # number of client companies
N_CONTACTS  = 520         # people at those companies
N_USERS     = 85          # internal agents / employees
N_DEALS     = 1850        # total opportunities (open + closed)
N_PRODUCTS  = 48          # service/talent catalogue items

# =============================================================================
# SETUP
# =============================================================================

random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

os.makedirs(OUTPUT_PATH, exist_ok=True)

START_DATE = date(START_YEAR, 1, 1)
END_DATE   = date(END_YEAR, 12, 31)

def rand_date(start=START_DATE, end=END_DATE):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def date_add(d, days):
    return d + timedelta(days=int(days))

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

print("=" * 70)
print("  Sales Win Predictor — Synthetic CRM Data Generator")
print("=" * 70)

# =============================================================================
# REFERENCE DATA
# =============================================================================

DIVISIONS = ['TalentEdge', 'CreativeMotion', 'PulseMedia', 'BrandVault']

REGIONS   = ['North America', 'Europe', 'India', 'Asia Pacific', 'Australia']

INDUSTRIES = [
    'Fashion & Apparel', 'Sportswear', 'Entertainment',
    'Beauty & Cosmetics', 'Consumer Electronics', 'Food & Beverage',
    'Automotive', 'Financial Services', 'Retail', 'Media & Publishing'
]

# Realistic brand names for accounts (anonymised — no real company names)
BRAND_NAMES = [
    'Apex Sportswear', 'NovaBrand Co.', 'Velox Fashion', 'Stratum Athletics',
    'PinnaCo Apparel', 'Luxe Cosmetics', 'Urban Gear Ltd', 'CrestLine Media',
    'Solaris Entertainment', 'Delta Retail', 'Orbit Consumer', 'PeakWear Group',
    'Cascade Beauty', 'Meridian Sports', 'Titan Apparel', 'Vantage Electronics',
    'Stellar Foods', 'Prism Media', 'Axiom Automotive', 'Zenith Financial',
    'Horizon Fashion', 'Summit Sportswear', 'Radiant Cosmetics', 'Aurora Retail',
    'Vertex Entertainment', 'Cobalt Apparel', 'Nexus Media Group', 'Ironclad Athletics',
    'Luminos Beauty', 'Quantum Consumer', 'Arcadia Fashion', 'Blaze Sportswear',
    'Crystal Cosmetics', 'Eclipse Entertainment', 'Fusion Apparel', 'Glacier Foods',
    'Helix Electronics', 'Indigo Media', 'Jupiter Automotive', 'Kestrel Financial',
    'Lynx Retail', 'Mosaic Fashion', 'Nova Athletics', 'Obsidian Apparel',
    'Paladin Consumer', 'Quartz Cosmetics', 'Raven Entertainment', 'Sapphire Sports',
    'Terra Fashion', 'Ultima Beauty', 'Valor Apparel', 'Westbridge Retail',
    'Xenon Media', 'Yield Consumer', 'Zephyr Athletics', 'Alchemy Fashion',
    'Bastion Sportswear', 'Citadel Cosmetics', 'Dusk Entertainment', 'Echo Retail',
    'Falcon Apparel', 'Greystone Media', 'Hydra Athletics', 'Icon Consumer',
    'Javelin Fashion', 'Koda Cosmetics', 'Legacy Entertainment', 'Matrix Apparel',
    'Nebula Sports', 'Opal Fashion', 'Phoenix Cosmetics', 'Quiver Retail',
    'Realm Athletics', 'Slate Entertainment', 'Trident Apparel', 'Umbra Media',
    'Vega Consumer', 'Wolf Fashion', 'Xara Sportswear', 'Yale Cosmetics',
    'Zinc Entertainment', 'Archon Retail', 'Bolt Athletics', 'Canvas Apparel',
    'Drift Fashion', 'Epoch Cosmetics', 'Flare Sports', 'Glade Media',
    'Haven Consumer', 'Iris Apparel', 'Jolt Entertainment', 'Knight Retail',
    'Lance Athletics', 'Mast Fashion', 'Neon Cosmetics', 'Oasis Sports',
    'Pact Apparel', 'Quill Media', 'Ridge Consumer', 'Scout Fashion',
    'Torque Athletics', 'Unity Cosmetics', 'Vortex Entertainment', 'Wave Retail',
    'Xtreme Sports', 'Yoke Fashion', 'Zeal Cosmetics',
    # Extra filler to reach N_ACCOUNTS
    'Amber Holdings', 'Bravo Consumer', 'Carbon Fashion', 'Dash Athletics',
    'Edge Cosmetics', 'Forge Entertainment', 'Globe Retail', 'Halo Sports',
    'Ignite Apparel', 'Jetset Media', 'Karma Consumer', 'Lumen Fashion',
    'Magnet Athletics', 'Niche Cosmetics', 'Onyx Entertainment', 'Pulse Retail',
    'Quest Fashion', 'Rust Sports', 'Surge Apparel', 'Trek Media',
    'Unison Consumer', 'Vapor Fashion', 'Wraith Athletics', 'Xcel Cosmetics',
    'Yarn Entertainment', 'Zest Retail', 'Apex2 Sports', 'Bliss Fashion',
    'Craft Cosmetics', 'Dune Entertainment', 'Ember Retail', 'Fuse Athletics',
    'Gem Apparel', 'Hive Media', 'Ink Consumer', 'Jade Fashion',
    'Kite Athletics', 'Lime Cosmetics', 'Muse Entertainment', 'Nest Retail',
    'Oak Sports', 'Petal Fashion', 'Quad Apparel', 'Reef Media',
    'Sand Consumer', 'Teal Fashion', 'Umber Athletics', 'Vent Cosmetics',
    'Whirl Entertainment', 'Xray Retail', 'Yawn Sports', 'Zero Fashion',
    'Alpha Consumer', 'Beta Athletics', 'Gamma Cosmetics', 'Delta Entertainment',
    'Epsilon Retail', 'Zeta Sports', 'Eta Fashion', 'Theta Apparel',
    'Iota Media', 'Kappa Consumer', 'Lambda Fashion', 'Mu Athletics',
    'Nu Cosmetics', 'Xi Entertainment', 'Omicron Retail', 'Pi Sports',
    'Rho Fashion', 'Sigma Apparel', 'Tau Media', 'Upsilon Consumer',
    'Phi Fashion', 'Chi Athletics', 'Psi Cosmetics', 'Omega Entertainment',
][:N_ACCOUNTS]

LEAD_SOURCES = [
    'Inbound Inquiry', 'Referral', 'Outbound Cold Call',
    'Conference / Event', 'Website Form', 'LinkedIn Outreach',
    'Existing Relationship', 'Partner Referral'
]

LOST_REASONS = [
    'Price too high', 'Chose competitor', 'Budget cut / cancelled',
    'No decision made', 'Timeline mismatch', 'Requirements changed',
    'Internal staffing issue', 'Deal went silent', 'Scope too complex'
]

JOB_TITLES_CLIENT = [
    'Chief Marketing Officer', 'VP Marketing', 'Marketing Director',
    'Brand Manager', 'Head of Partnerships', 'Procurement Director',
    'VP Creative', 'Creative Director', 'Head of Campaigns',
    'Global Brand Lead', 'Senior Brand Manager', 'VP Commercial',
    'Licensing Director', 'Head of Brand Licensing', 'Chief Brand Officer'
]

# Internal user roles by division
USER_ROLES = {
    'TalentEdge':    ['Talent Agent', 'Senior Talent Agent', 'Agent Director', 'Junior Agent'],
    'CreativeMotion':['Content Agent', 'Senior Content Agent', 'Agent Director', 'Junior Agent'],
    'PulseMedia':    ['Marketing Manager', 'Senior Account Manager',
                      'Account Director', 'Account Associate'],
    'BrandVault':    ['Licensing Agent', 'Senior Licensing Agent',
                      'Licensing Director', 'Junior Licensing Agent'],
    'Management':    ['VP Sales', 'Head of Operations', 'Sales Operations Analyst'],
}

SENIORITY_MAP = {
    'Junior Agent': 1, 'Account Associate': 1, 'Junior Licensing Agent': 1,
    'Talent Agent': 2, 'Content Agent': 2, 'Marketing Manager': 2, 'Licensing Agent': 2,
    'Senior Talent Agent': 3, 'Senior Content Agent': 3,
    'Senior Account Manager': 3, 'Senior Licensing Agent': 3,
    'Agent Director': 4, 'Account Director': 4, 'Licensing Director': 4,
    'VP Sales': 5, 'Head of Operations': 5, 'Sales Operations Analyst': 2,
}

STAGES_IN_ORDER = [
    'Lead', 'Qualified Lead', 'Opportunity', 'Negotiation', 'Closed Won', 'Closed Lost'
]

# ─────────────────────────────────────────────────────────────────────────────
# LINE ITEM TYPES PER DIVISION
# ─────────────────────────────────────────────────────────────────────────────
LINE_ITEM_TYPES = {
    'TalentEdge': [
        ('Model - Day Rate',       'per day',   2500, 18000),
        ('Photographer - Day Rate','per day',   2200,  8000),
        ('Stylist - Day Rate',     'per day',   1500,  5500),
        ('Makeup Artist - Day Rate','per day',  1200,  4500),
        ('Creative Director - Day Rate','per day', 2800, 9500),
        ('Usage Rights - Print',   'flat fee', 3000, 25000),
        ('Usage Rights - Digital', 'flat fee', 2000, 18000),
        ('Usage Rights - Global',  'flat fee', 8000, 60000),
        ('Production - Location Rental','flat fee', 1500, 12000),
    ],
    'CreativeMotion': [
        ('Scriptwriter - Project', 'flat fee',  5000, 35000),
        ('Director - Day Rate',    'per day',   3500, 12000),
        ('Designer - Day Rate',    'per day',   1800,  6000),
        ('Content Writer - Day Rate','per day', 1000,  3500),
        ('Post-Production Fee',    'flat fee',  8000, 50000),
        ('Video Production Package','flat fee',15000,120000),
        ('Photography Package',    'flat fee',  6000, 45000),
    ],
    'PulseMedia': [
        ('Campaign Strategy Fee',  'flat fee',  8000, 60000),
        ('Digital Marketing - Hourly','per hour', 95,  250),
        ('Social Media Management', 'per month',3500, 18000),
        ('Media Planning & Buying', 'flat fee', 12000,80000),
        ('Branding & Identity',     'flat fee', 10000,75000),
        ('Event Marketing',         'flat fee',  8000,55000),
        ('Content Creation Package','flat fee',  6000,40000),
        ('Analytics & Reporting',   'per month', 2500,12000),
    ],
    'BrandVault': [
        ('Brand License - Minimum Guarantee','flat fee', 50000, 800000),
        ('Royalty Agreement Setup', 'flat fee',  5000, 25000),
        ('Trademark License Fee',   'flat fee', 20000,200000),
        ('Character License - MG',  'flat fee', 80000, 600000),
        ('Sports Logo License',     'flat fee', 40000, 350000),
        ('Territory Rights Fee',    'flat fee', 10000, 120000),
        ('License Renewal Fee',     'flat fee', 15000, 150000),
    ],
}

ACTIVITY_TYPES    = ['Email', 'Phone Call', 'Video Meeting', 'In-Person Meeting', 'Demo', 'Proposal Sent']
ACTIVITY_OUTCOMES = ['Positive - Follow up scheduled', 'Neutral - Information shared',
                      'Positive - Client interested', 'Negative - Client hesitant',
                      'Positive - Moving to next stage', None]

print("  Reference data loaded.")

# =============================================================================
# TABLE 1: crm_accounts  (Client companies — the brands)
# =============================================================================
print("\n  [1/9] Generating crm_accounts...")

accounts = []
for i in range(N_ACCOUNTS):
    industry   = random.choice(INDUSTRIES)
    region     = random.choice(REGIONS)
    country_map = {
        'North America': random.choice(['United States', 'Canada']),
        'Europe':        random.choice(['United Kingdom', 'Germany', 'France', 'Italy', 'Netherlands']),
        'India':         'India',
        'Asia Pacific':  random.choice(['Japan', 'South Korea', 'Singapore', 'China']),
        'Australia':     'Australia',
    }
    country = country_map[region]
    created = rand_date(START_DATE, date(2022, 12, 31))

    # Annual revenue band drives client tier
    rev_band = random.choices(
        ['Under $10M', '$10M to $100M', '$100M to $500M', '$500M to $1B', 'Over $1B'],
        weights=[15, 30, 30, 15, 10]
    )[0]
    tier_map = {
        'Under $10M': 3, '$10M to $100M': 3, '$100M to $500M': 2,
        '$500M to $1B': 1, 'Over $1B': 1
    }
    tier = tier_map[rev_band]

    accounts.append({
        # ── COLUMN DESCRIPTIONS ──────────────────────────────────────────
        # account_id          : Unique CRM ID for this company
        # account_name        : Name of the client brand / company
        # industry            : The sector this brand operates in
        # country             : Country of the company's headquarters
        # region              : Broad geographic region (used for regional pricing)
        # annual_revenue_band : Approximate annual revenue bracket of the client
        # account_type        : Whether this is a new Prospect or an existing Customer
        # account_tier        : 1 = Top client (highest spend), 2 = Mid, 3 = Small
        # number_of_employees : Approximate headcount (proxy for company size)
        # is_active           : 1 = Currently active in CRM, 0 = Churned/inactive
        # created_date        : When this account was first entered into the CRM
        # last_activity_date  : Last time any deal or interaction was logged (set later)
        'account_id':           f'ACC-{1000 + i}',
        'account_name':         BRAND_NAMES[i],
        'industry':             industry,
        'country':              country,
        'region':               region,
        'annual_revenue_band':  rev_band,
        'account_type':         random.choices(['Prospect', 'Customer'], weights=[40, 60])[0],
        'account_tier':         tier,
        'number_of_employees':  random.choice([50, 200, 500, 1000, 5000, 10000, 50000]),
        'is_active':            random.choices([1, 0], weights=[90, 10])[0],
        'created_date':         created.strftime('%Y-%m-%d'),
        'last_activity_date':   None,   # filled later
    })

df_accounts = pd.DataFrame(accounts)
df_accounts.to_csv(os.path.join(OUTPUT_PATH, 'crm_accounts.csv'), index=False)
print(f"     crm_accounts.csv — {len(df_accounts)} rows")

# =============================================================================
# TABLE 2: crm_contacts  (Individual people at client companies)
# =============================================================================
print("  [2/9] Generating crm_contacts...")

contacts = []
account_ids = df_accounts['account_id'].tolist()
for i in range(N_CONTACTS):
    account_id = random.choice(account_ids)
    created    = rand_date(START_DATE, date(2023, 6, 30))
    contacts.append({
        # contact_id          : Unique CRM ID for this person
        # account_id          : Which company they work for (FK → crm_accounts)
        # first_name          : First name
        # last_name           : Last name
        # email               : Work email address
        # job_title           : Their role at the client company
        # department          : Which team/department they are in
        # is_primary_contact  : 1 = the main point of contact for deals with this company
        # is_decision_maker   : 1 = has budget authority (can say yes/no to a deal)
        # created_date        : When this contact was added to the CRM
        # is_active           : 1 = still at the company / contactable
        'contact_id':         f'CON-{2000 + i}',
        'account_id':         account_id,
        'first_name':         fake.first_name(),
        'last_name':          fake.last_name(),
        'email':              fake.company_email(),
        'job_title':          random.choice(JOB_TITLES_CLIENT),
        'department':         random.choice(['Marketing', 'Brand', 'Procurement',
                                              'Creative', 'Commercial', 'Licensing']),
        'is_primary_contact': random.choices([1, 0], weights=[40, 60])[0],
        'is_decision_maker':  random.choices([1, 0], weights=[35, 65])[0],
        'created_date':       created.strftime('%Y-%m-%d'),
        'is_active':          random.choices([1, 0], weights=[85, 15])[0],
    })

df_contacts = pd.DataFrame(contacts)
df_contacts.to_csv(os.path.join(OUTPUT_PATH, 'crm_contacts.csv'), index=False)
print(f"     crm_contacts.csv — {len(df_contacts)} rows")

# =============================================================================
# TABLE 3: crm_users  (Internal agents and employees)
# =============================================================================
print("  [3/9] Generating crm_users...")

users = []
user_id_counter = 3000

for division, roles in USER_ROLES.items():
    if division == 'Management':
        count = 5
    elif division == 'PulseMedia':
        count = 25   # marketing agency has most staff
    else:
        count = 18   # talent/licensing divisions

    for _ in range(count):
        role      = random.choice(roles)
        seniority = SENIORITY_MAP.get(role, 2)
        region    = random.choice(REGIONS)
        hire_date = rand_date(date(2010, 1, 1), date(2023, 6, 30))

        users.append({
            # user_id          : Unique internal user ID
            # first_name/last_name : Agent's name
            # email            : Internal company email
            # role             : Job title within the company
            # division         : Which business unit they belong to
            # region           : Their primary operating region
            # seniority_level  : 1=Junior, 2=Mid, 3=Senior, 4=Director, 5=VP
            # hire_date        : When they joined the company
            # is_active        : 1 = still employed
            # manager_id       : Their manager's user_id (filled in second pass)
            # target_deals_per_year : Annual deal target for this agent
            'user_id':                f'USR-{user_id_counter}',
            'first_name':             fake.first_name(),
            'last_name':              fake.last_name(),
            'email':                  fake.company_email(),
            'role':                   role,
            'division':               division,
            'region':                 region,
            'seniority_level':        seniority,
            'hire_date':              hire_date.strftime('%Y-%m-%d'),
            'is_active':              random.choices([1, 0], weights=[80, 20])[0],
            'manager_id':             None,   # filled below
            'target_deals_per_year':  random.choice([10, 15, 20, 25, 30]),
        })
        user_id_counter += 1

df_users = pd.DataFrame(users)

# Assign managers (directors manage agents within same division)
directors = df_users[df_users['seniority_level'] >= 4]['user_id'].tolist()
for idx, row in df_users.iterrows():
    if row['seniority_level'] < 4 and directors:
        df_users.at[idx, 'manager_id'] = random.choice(directors)

df_users.to_csv(os.path.join(OUTPUT_PATH, 'crm_users.csv'), index=False)
print(f"     crm_users.csv — {len(df_users)} rows")

# Pre-build user lookup for deal generation
user_list = df_users[df_users['is_active'] == 1].to_dict('records')
user_by_division = {div: [u for u in user_list if u['division'] == div]
                    for div in DIVISIONS}
# Fallback: any user
for div in DIVISIONS:
    if not user_by_division[div]:
        user_by_division[div] = user_list[:5]

# =============================================================================
# TABLE 9: crm_products  (Service / talent catalogue)
# =============================================================================
print("  [4/9] Generating crm_products...")

products = []
prod_id_counter = 9000
for division, items in LINE_ITEM_TYPES.items():
    for name, unit, price_low, price_high in items:
        products.append({
            # product_id             : Unique product/service catalogue ID
            # product_name           : Name of the service or talent type
            # product_category       : Broad category
            # division               : Which business division offers this
            # standard_unit_price    : Catalogue base price (before negotiation)
            # unit_type              : How it is priced (per day, per hour, flat fee)
            # price_range_low        : Minimum realistic price for this product
            # price_range_high       : Maximum realistic price for this product
            # is_active              : 1 = still offered in catalogue
            # created_date           : When this product was added
            'product_id':           f'PRD-{prod_id_counter}',
            'product_name':         name,
            'product_category':     name.split(' - ')[0].split(' - ')[0],
            'division':             division,
            'standard_unit_price':  round((price_low + price_high) / 2, -2),
            'unit_type':            unit,
            'price_range_low':      price_low,
            'price_range_high':     price_high,
            'is_active':            1,
            'created_date':         rand_date(date(2012, 1, 1), date(2016, 12, 31)).strftime('%Y-%m-%d'),
        })
        prod_id_counter += 1

df_products = pd.DataFrame(products)
df_products.to_csv(os.path.join(OUTPUT_PATH, 'crm_products.csv'), index=False)
print(f"     crm_products.csv — {len(df_products)} rows")

# =============================================================================
# TABLE 4: crm_opportunities  (THE MAIN DEALS TABLE)
# =============================================================================
print("  [5/9] Generating crm_opportunities...")

# Track repeat client deals for feature engineering
account_deal_history = {acc_id: [] for acc_id in account_ids}

opportunities = []
opp_id_counter = 4000

for i in range(N_DEALS):
    # ── Pick division & assign realistic deal properties ───────────────────
    division = random.choices(
        DIVISIONS,
        weights=[28, 18, 35, 19]   # PulseMedia gets most volume
    )[0]

    region = random.choice(REGIONS)
    account = random.choice(accounts)
    account_id = account['account_id']

    # Pick an agent from matching division
    div_users = user_by_division.get(division, user_list[:5])
    agent = random.choice(div_users)

    # ── Deal created date (weighted toward more recent years) ──────────────
    year_weights = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # 2015–2024 increasing
    year  = random.choices(range(2015, 2025), weights=year_weights)[0]
    month = random.choices(
        range(1, 13),
        weights=[6,6,8,8,8,8,9,9,10,10,12,12]  # Q4 heavier
    )[0]
    day   = random.randint(1, 28)
    created_date = date(year, month, day)

    if created_date > END_DATE:
        created_date = END_DATE

    # ── Deal type: renewals are more common for repeat clients ─────────────
    prior_deals = len(account_deal_history[account_id])
    is_renewal  = 1 if (prior_deals >= 1 and random.random() < 0.4) else 0
    deal_type   = 'Renewal' if is_renewal else random.choices(
        ['New Business', 'Upsell', 'Cross-sell'],
        weights=[70, 20, 10]
    )[0]

    # ── Deal value by division ─────────────────────────────────────────────
    value_ranges = {
        'TalentEdge':    (15000,  280000),
        'CreativeMotion':(25000,  350000),
        'PulseMedia':    (30000,  500000),
        'BrandVault':    (80000, 1200000),
    }
    lo, hi = value_ranges[division]
    # Skew: most deals are small, some are large
    raw_value = np.random.lognormal(mean=np.log((lo + hi) / 2.5), sigma=0.6)
    deal_value = float(np.clip(raw_value, lo, hi))
    deal_value = round(deal_value / 500) * 500   # round to nearest $500

    # ── Discount percentage ────────────────────────────────────────────────
    # Most deals have 5–20% discount; a tail has 25–40%
    discount_pct = float(np.clip(
        np.random.lognormal(mean=np.log(12), sigma=0.5), 0, 42
    ))
    discount_pct = round(discount_pct, 1)

    # ── Agent attributes for win probability ──────────────────────────────
    seniority       = agent['seniority_level']
    is_specialist   = 1 if agent['division'] == division else 0
    agent_deals_count = len([o for o in opportunities
                              if o['owner_user_id'] == agent['user_id']
                              and o.get('close_date_actual') is None])
    agent_overloaded = 1 if agent_deals_count > 30 else 0

    # ── Build win probability via logistic formula ─────────────────────────
    # Each coefficient reflects a real business hypothesis
    log_odds = (
          0.30                                   # base rate intercept (~43% win)
        - 0.018 * max(0, discount_pct - 15)      # >15% discount hurts
        + 0.55  * is_renewal                     # renewals win more often
        + 0.30  * (1 if prior_deals >= 2 else 0) # repeat clients win more
        + 0.22  * is_specialist                  # specialist agent advantage
        + 0.18  * (seniority - 2)                # senior agents better
        - 0.40  * agent_overloaded               # overloaded agent hurts
        + 0.20  * (1 if division == 'PulseMedia' else 0)  # marketing closes more
        - 0.25  * (1 if division == 'BrandVault' else 0)  # licensing is harder
        + 0.15  * (1 if month in [11, 12, 3, 6, 9] else 0)  # fiscal-end boost
        + np.random.normal(0, 0.4)               # realistic noise
    )
    win_prob = sigmoid(log_odds)

    # ── Determine outcome and funnel progression ───────────────────────────
    # Deals in last 6 months can still be open
    months_since_created = (END_DATE - created_date).days / 30.0
    is_open = (months_since_created < 5) and (random.random() < 0.35)

    if is_open:
        is_won        = None
        final_stage   = random.choices(
            ['Lead', 'Qualified Lead', 'Opportunity', 'Negotiation'],
            weights=[10, 20, 40, 30]
        )[0]
        close_actual  = None
        lost_reason   = None
    else:
        is_won      = 1 if random.random() < win_prob else 0
        final_stage = 'Closed Won' if is_won else 'Closed Lost'

        # How long did it take to close?
        avg_days_map = {
            'TalentEdge': 35, 'CreativeMotion': 42,
            'PulseMedia': 50, 'BrandVault': 65
        }
        avg_days  = avg_days_map[division]
        days_mult = 1.0 if is_won else random.uniform(1.1, 2.0)
        days_to_close = int(np.random.normal(avg_days * days_mult, avg_days * 0.3))
        days_to_close = max(5, days_to_close)

        close_actual = date_add(created_date, days_to_close)
        if close_actual > END_DATE:
            close_actual = END_DATE
        close_actual = close_actual.strftime('%Y-%m-%d')

        lost_reason = random.choice(LOST_REASONS) if is_won == 0 else None

    # Expected close date (what the agent entered at deal creation)
    exp_days    = random.randint(20, 90)
    exp_close   = date_add(created_date, exp_days).strftime('%Y-%m-%d')

    # ── Contact assigned ───────────────────────────────────────────────────
    acct_contacts = [c for c in contacts if c['account_id'] == account_id]
    primary_contact_id = random.choice(acct_contacts)['contact_id'] if acct_contacts else None

    # ── Fiscal year and quarter ────────────────────────────────────────────
    fiscal_q = f"Q{(created_date.month - 1) // 3 + 1}"

    # ── Append deal ───────────────────────────────────────────────────────
    opp_name = f"{account['account_name']} - {division} - {deal_type} - {year}"
    opp = {
        # opportunity_id       : Unique CRM ID for this deal (e.g. OPP-4000)
        # opportunity_name     : Human-readable deal name
        # account_id           : Which client company this deal is for (FK → crm_accounts)
        # primary_contact_id   : Main person at the client we are talking to (FK → crm_contacts)
        # owner_user_id        : Internal agent responsible for this deal (FK → crm_users)
        # division             : Which business division owns this deal
        # region               : Geographic region this deal operates in
        # deal_type            : New Business / Renewal / Upsell / Cross-sell
        # lead_source          : How this lead was generated
        # stage                : Current CRM stage at time of data export
        # amount               : Total deal value in USD at the time of closing or last update
        # discount_pct         : Discount % being offered to the client
        # probability_manual   : Win probability % manually entered by the agent in CRM
        # created_date         : Date the deal was first created in the CRM
        # expected_close_date  : Target close date set by the agent at deal creation
        # close_date_actual    : Actual date the deal closed (NULL if still open)
        # is_won               : 1 = Deal won, 0 = Deal lost, NULL = Still open
        # lost_reason          : Why the deal was lost (NULL if won or still open)
        # is_renewal           : 1 = this is a contract renewal, 0 = new deal
        # fiscal_year          : Fiscal year the deal was created in
        # fiscal_quarter       : Fiscal quarter the deal was created in
        # is_open              : 1 = deal still active, 0 = closed
        'opportunity_id':       f'OPP-{opp_id_counter}',
        'opportunity_name':     opp_name,
        'account_id':           account_id,
        'primary_contact_id':   primary_contact_id,
        'owner_user_id':        agent['user_id'],
        'division':             division,
        'region':               region,
        'deal_type':            deal_type,
        'lead_source':          random.choice(LEAD_SOURCES),
        'stage':                final_stage,
        'amount':               deal_value,
        'discount_pct':         discount_pct,
        'probability_manual':   round(random.uniform(20, 80), 0),  # agent's gut feel
        'created_date':         created_date.strftime('%Y-%m-%d'),
        'expected_close_date':  exp_close,
        'close_date_actual':    close_actual,
        'is_won':               is_won,
        'lost_reason':          lost_reason,
        'is_renewal':           is_renewal,
        'fiscal_year':          year,
        'fiscal_quarter':       fiscal_q,
        'is_open':              1 if is_open else 0,
    }
    opportunities.append(opp)
    account_deal_history[account_id].append(opp_id_counter)
    opp_id_counter += 1

df_opps = pd.DataFrame(opportunities)
df_opps.to_csv(os.path.join(OUTPUT_PATH, 'crm_opportunities.csv'), index=False)
closed_won  = df_opps[df_opps['is_won'] == 1].shape[0]
closed_lost = df_opps[df_opps['is_won'] == 0].shape[0]
open_deals  = df_opps[df_opps['is_open'] == 1].shape[0]
win_rate    = closed_won / (closed_won + closed_lost) * 100
print(f"     crm_opportunities.csv — {len(df_opps)} rows")
print(f"       Won: {closed_won}  |  Lost: {closed_lost}  |  Open: {open_deals}")
print(f"       Win rate (closed only): {win_rate:.1f}%")

# =============================================================================
# TABLE 5: crm_opportunity_line_items
# =============================================================================
print("  [6/9] Generating crm_opportunity_line_items...")

line_items = []
li_id_counter = 5000

for _, opp in df_opps.iterrows():
    division    = opp['division']
    prod_items  = LINE_ITEM_TYPES[division]
    opp_value   = opp['amount']
    disc        = opp['discount_pct'] / 100.0

    # Number of line items: complexity varies. BrandVault tends to be simpler.
    n_li_map = {'TalentEdge': (2,7), 'CreativeMotion': (2,6),
                 'PulseMedia': (3,8), 'BrandVault': (1,4)}
    lo_li, hi_li = n_li_map[division]
    n_items = random.randint(lo_li, hi_li)

    # Pick n unique product types
    chosen = random.sample(prod_items, min(n_items, len(prod_items)))

    # Scale prices so they roughly sum to deal amount
    raw_prices = []
    for name, unit, plo, phi in chosen:
        if unit == 'per day':
            qty   = random.randint(1, 10)
            price = random.randint(plo, phi)
        elif unit == 'per hour':
            qty   = random.randint(10, 120)
            price = random.randint(plo, phi)
        elif unit == 'per month':
            qty   = random.randint(1, 6)
            price = random.randint(plo, phi)
        else:  # flat fee
            qty   = 1
            price = random.randint(plo, phi)
        raw_prices.append((name, unit, price, qty))

    raw_total = sum(p * q for _, _, p, q in raw_prices)
    scale     = opp_value / raw_total if raw_total > 0 else 1.0

    for (name, unit, price, qty) in raw_prices:
        adj_price  = round(price * scale, 2)
        line_disc  = round(random.uniform(0, disc * 1.5), 3)
        net        = round(adj_price * qty * (1 - line_disc), 2)

        # Find matching product_id
        matched = df_products[
            (df_products['product_name'] == name) &
            (df_products['division'] == division)
        ]
        prod_id = matched['product_id'].values[0] if len(matched) > 0 else 'PRD-UNKNOWN'

        line_items.append({
            # line_item_id         : Unique ID for this line item
            # opportunity_id       : Which deal this line item belongs to (FK → crm_opportunities)
            # product_id           : Which service/talent from the catalogue (FK → crm_products)
            # line_item_name       : Human-readable name of the item (e.g. "Model - Day Rate")
            # line_item_type       : Category (Talent Day Rate, Usage Rights, Billable Hours, etc.)
            # unit_type            : How it is priced: per day, per hour, flat fee, per month
            # unit_price           : Price per single unit (e.g. per day or per hour)
            # quantity             : Number of units (days, hours, months, or 1 for flat fee)
            # gross_amount         : unit_price × quantity (before discount)
            # discount_applied_pct : Discount applied specifically to this line item (%)
            # net_amount           : Final charged amount after discount
            # is_negotiated        : 1 = price was negotiated down from catalogue, 0 = standard
            # created_date         : When this line item was added to the deal
            'line_item_id':         f'LI-{li_id_counter}',
            'opportunity_id':       opp['opportunity_id'],
            'product_id':           prod_id,
            'line_item_name':       name,
            'line_item_type':       name.split(' - ')[0] if ' - ' in name else name,
            'unit_type':            unit,
            'unit_price':           adj_price,
            'quantity':             qty,
            'gross_amount':         round(adj_price * qty, 2),
            'discount_applied_pct': round(line_disc * 100, 2),
            'net_amount':           net,
            'is_negotiated':        1 if line_disc > 0.05 else 0,
            'created_date':         opp['created_date'],
        })
        li_id_counter += 1

df_line_items = pd.DataFrame(line_items)
df_line_items.to_csv(os.path.join(OUTPUT_PATH, 'crm_opportunity_line_items.csv'), index=False)
print(f"     crm_opportunity_line_items.csv — {len(df_line_items)} rows")

# =============================================================================
# TABLE 6: crm_opportunity_stage_history
# =============================================================================
print("  [7/9] Generating crm_opportunity_stage_history...")

stage_history = []
sh_id_counter = 6000

stage_order = ['Lead', 'Qualified Lead', 'Opportunity', 'Negotiation']

avg_days_per_stage = {
    'Lead':          (2, 12),
    'Qualified Lead':(5, 20),
    'Opportunity':   (10, 35),
    'Negotiation':   (7, 28),
}

for _, opp in df_opps.iterrows():
    final_stage = opp['stage']
    opp_created = datetime.strptime(opp['created_date'], '%Y-%m-%d').date()
    is_won      = opp['is_won']
    owner_id    = opp['owner_user_id']

    if final_stage in ('Closed Won', 'Closed Lost'):
        stages_reached = stage_order.copy()
    else:
        try:
            cut = stage_order.index(final_stage) + 1
        except ValueError:
            cut = 2
        stages_reached = stage_order[:cut]

    current_date = opp_created
    prev_stage   = None

    for j, stage in enumerate(stages_reached):
        lo_d, hi_d   = avg_days_per_stage[stage]
        # Lost deals spend more time in later stages (stalling)
        if is_won == 0 and stage in ('Negotiation', 'Opportunity'):
            hi_d = int(hi_d * 1.8)
        days_in_stage = random.randint(lo_d, hi_d)

        entered_date = current_date
        exited_date  = date_add(entered_date, days_in_stage)
        if exited_date > END_DATE:
            exited_date = END_DATE

        if j < len(stages_reached) - 1:
            to_stage   = stages_reached[j + 1]
            exited_str = exited_date.strftime('%Y-%m-%d')
        else:
            to_stage   = final_stage
            if final_stage in ('Closed Won', 'Closed Lost'):
                exited_str = opp['close_date_actual']
            else:
                exited_str = None  # still in this stage

        stage_history.append({
            # stage_history_id  : Unique ID for this stage transition record
            # opportunity_id    : Which deal (FK → crm_opportunities)
            # from_stage        : Previous stage (NULL if this is the first entry)
            # to_stage          : Stage the deal moved INTO
            # stage_entered_date: Date the deal entered this stage
            # stage_exited_date : Date the deal left this stage (NULL if current stage)
            # days_in_stage     : Number of days spent in this stage
            # changed_by_user_id: Who made the stage change in the CRM
            # is_regression     : 1 = deal moved BACKWARDS in the funnel (rare but important)
            'stage_history_id':   f'SH-{sh_id_counter}',
            'opportunity_id':     opp['opportunity_id'],
            'from_stage':         prev_stage,
            'to_stage':           to_stage if j < len(stages_reached) - 1 else stage,
            'stage_entered_date': entered_date.strftime('%Y-%m-%d'),
            'stage_exited_date':  exited_str,
            'days_in_stage':      days_in_stage,
            'changed_by_user_id': owner_id,
            'is_regression':      0,
        })
        sh_id_counter += 1
        prev_stage    = stage
        current_date  = exited_date

    # Occasionally add a regression (deal moves back a stage)
    if random.random() < 0.05 and len(stages_reached) > 1:
        stage_history.append({
            'stage_history_id':   f'SH-{sh_id_counter}',
            'opportunity_id':     opp['opportunity_id'],
            'from_stage':         stages_reached[-1],
            'to_stage':           stages_reached[-2],
            'stage_entered_date': date_add(current_date, random.randint(1, 5)).strftime('%Y-%m-%d'),
            'stage_exited_date':  None,
            'days_in_stage':      None,
            'changed_by_user_id': owner_id,
            'is_regression':      1,
        })
        sh_id_counter += 1

df_stage_history = pd.DataFrame(stage_history)
df_stage_history.to_csv(os.path.join(OUTPUT_PATH, 'crm_opportunity_stage_history.csv'), index=False)
print(f"     crm_opportunity_stage_history.csv — {len(df_stage_history)} rows")

# =============================================================================
# TABLE 7: crm_activities  (Emails, calls, meetings per deal)
# =============================================================================
print("  [8/9] Generating crm_activities...")

activities = []
act_id_counter = 7000

for _, opp in df_opps.iterrows():
    opp_created = datetime.strptime(opp['created_date'], '%Y-%m-%d').date()
    final_stage = opp['stage']
    is_won      = opp['is_won']

    # Number of activities: more for complex/longer deals
    n_activities_map = {
        'Lead': 1, 'Qualified Lead': 3,
        'Opportunity': 5, 'Negotiation': 7,
        'Closed Won': 8, 'Closed Lost': 5,
    }
    n_acts = random.randint(
        max(1, n_activities_map.get(final_stage, 4) - 2),
        n_activities_map.get(final_stage, 4) + 3
    )

    close_ref = opp['close_date_actual']
    end_ref   = datetime.strptime(close_ref, '%Y-%m-%d').date() if close_ref else END_DATE

    last_act_date = opp_created
    for k in range(n_acts):
        act_date = date_add(last_act_date, random.randint(1, 14))
        if act_date > end_ref:
            act_date = end_ref
        last_act_date = act_date

        act_type = random.choices(
            ACTIVITY_TYPES,
            weights=[30, 25, 20, 10, 8, 7]
        )[0]

        # Outcome is better for won deals
        if is_won == 1:
            outcome_weights = [40, 20, 25, 5, 8, 2]
        else:
            outcome_weights = [15, 25, 15, 25, 8, 12]

        activities.append({
            # activity_id        : Unique ID for this interaction record
            # opportunity_id     : Which deal this activity is logged against (FK → crm_opportunities)
            # user_id            : Which agent logged this activity (FK → crm_users)
            # activity_type      : Type of interaction: Email / Phone Call / Meeting / Demo / etc.
            # subject            : Brief description of what the interaction was about
            # activity_date      : Date the activity took place
            # duration_minutes   : How long the call or meeting lasted (NULL for emails)
            # outcome            : Result of the interaction (positive, neutral, negative)
            # is_outbound        : 1 = agent contacted client, 0 = client reached out first
            # days_since_deal_created : How many days into the deal lifecycle this happened
            'activity_id':          f'ACT-{act_id_counter}',
            'opportunity_id':       opp['opportunity_id'],
            'user_id':              opp['owner_user_id'],
            'activity_type':        act_type,
            'subject':              f'{act_type} re: {opp["opportunity_name"][:40]}',
            'activity_date':        act_date.strftime('%Y-%m-%d'),
            'duration_minutes':     random.choice([15, 30, 45, 60, 90, None])
                                    if act_type != 'Email' else None,
            'outcome':              random.choices(ACTIVITY_OUTCOMES, weights=outcome_weights)[0],
            'is_outbound':          random.choices([1, 0], weights=[65, 35])[0],
            'days_since_deal_created': (act_date - opp_created).days,
        })
        act_id_counter += 1

df_activities = pd.DataFrame(activities)
df_activities.to_csv(os.path.join(OUTPUT_PATH, 'crm_activities.csv'), index=False)
print(f"     crm_activities.csv — {len(df_activities)} rows")

# =============================================================================
# TABLE 8: crm_contracts  (Won deals only)
# =============================================================================
print("  [9/9] Generating crm_contracts...")

contracts = []
con_id_counter = 8000
won_opps = df_opps[df_opps['is_won'] == 1]

for _, opp in won_opps.iterrows():
    signed_date  = datetime.strptime(opp['close_date_actual'], '%Y-%m-%d').date()
    duration_mo  = random.choice([6, 12, 18, 24, 36])
    end_date_c   = date_add(signed_date, duration_mo * 30)

    # BrandVault licensing contracts have royalty clauses
    has_royalty   = 1 if opp['division'] == 'BrandVault' else 0
    royalty_pct   = round(random.uniform(5, 15), 1) if has_royalty else None
    royalty_thresh= round(opp['amount'] * 1.3, -3) if has_royalty else None

    contracts.append({
        # contract_id           : Unique ID for this contract
        # opportunity_id        : The deal this contract was created from (FK → crm_opportunities)
        # account_id            : Which client signed (FK → crm_accounts)
        # contract_start_date   : When the contract becomes active
        # contract_end_date     : When the contract expires
        # contract_duration_months : Length of the contract in months
        # contract_value        : Total agreed value (matches deal amount)
        # payment_terms         : When and how the client pays
        # signed_date           : Date the contract was counter-signed
        # contract_status       : Active / Expired / Renewed / Cancelled
        # has_royalty_clause    : 1 = BrandVault deal with royalty % on sales
        # royalty_pct           : Percentage of net sales above threshold (if applicable)
        # royalty_threshold_usd : Net sales amount above which royalty kicks in
        # number_of_revisions   : How many times the contract was redrafted before signing
        'contract_id':            f'CON-{con_id_counter}',
        'opportunity_id':         opp['opportunity_id'],
        'account_id':             opp['account_id'],
        'contract_start_date':    signed_date.strftime('%Y-%m-%d'),
        'contract_end_date':      end_date_c.strftime('%Y-%m-%d'),
        'contract_duration_months': duration_mo,
        'contract_value':         opp['amount'],
        'payment_terms':          random.choice(['Net 30', 'Net 60', '50% upfront / 50% on delivery',
                                                  'Monthly instalments', 'Upon signing']),
        'signed_date':            signed_date.strftime('%Y-%m-%d'),
        'contract_status':        random.choices(
            ['Active', 'Expired', 'Renewed', 'Cancelled'],
            weights=[40, 35, 20, 5]
        )[0],
        'has_royalty_clause':     has_royalty,
        'royalty_pct':            royalty_pct,
        'royalty_threshold_usd':  royalty_thresh,
        'number_of_revisions':    random.randint(0, 5),
    })
    con_id_counter += 1

df_contracts = pd.DataFrame(contracts)
df_contracts.to_csv(os.path.join(OUTPUT_PATH, 'crm_contracts.csv'), index=False)
print(f"     crm_contracts.csv — {len(df_contracts)} rows")

# =============================================================================
# UPDATE last_activity_date on accounts
# =============================================================================
last_act = df_activities.groupby(
    df_opps.set_index('opportunity_id')
    .loc[df_activities['opportunity_id'], 'account_id']
    .values
)['activity_date'].max().reset_index()
last_act.columns = ['account_id', 'last_activity_date']
df_accounts = df_accounts.merge(last_act, on='account_id', how='left',
                                 suffixes=('_old', ''))
df_accounts.drop(columns=['last_activity_date_old'], errors='ignore', inplace=True)
df_accounts.to_csv(os.path.join(OUTPUT_PATH, 'crm_accounts.csv'), index=False)

# =============================================================================
# SUMMARY REPORT
# =============================================================================
print("\n" + "=" * 70)
print("  GENERATION COMPLETE")
print("=" * 70)
print(f"\n  Output folder : {OUTPUT_PATH}\n")

summary = [
    ('crm_accounts.csv',                    len(df_accounts),    'Client companies / brands'),
    ('crm_contacts.csv',                    len(df_contacts),    'People at client companies'),
    ('crm_users.csv',                       len(df_users),       'Internal agents & employees'),
    ('crm_opportunities.csv',               len(df_opps),        'Deals (MAIN TABLE)'),
    ('crm_opportunity_line_items.csv',      len(df_line_items),  'Billable items per deal'),
    ('crm_opportunity_stage_history.csv',   len(df_stage_history),'Stage transitions per deal'),
    ('crm_activities.csv',                  len(df_activities),  'Emails, calls, meetings'),
    ('crm_contracts.csv',                   len(df_contracts),   'Contract records (won deals)'),
    ('crm_products.csv',                    len(df_products),    'Service & talent catalogue'),
]
total_rows = sum(r for _, r, _ in summary)

print(f"  {'File':<48} {'Rows':>7}   Description")
print(f"  {'-'*48} {'-'*7}   {'-'*30}")
for fname, rows, desc in summary:
    print(f"  {fname:<48} {rows:>7,}   {desc}")
print(f"  {'':48} {'-'*7}")
print(f"  {'TOTAL ROWS':<48} {total_rows:>7,}")

print(f"""
  Dataset Stats:
    Date range       : {START_YEAR}–{END_YEAR} (10 years)
    Won deals        : {closed_won:,}
    Lost deals       : {closed_lost:,}
    Open deals       : {open_deals:,}
    Win rate         : {win_rate:.1f}% (closed deals only)
    Avg line items/deal : {len(df_line_items)/len(df_opps):.1f}
    Avg activities/deal : {len(df_activities)/len(df_opps):.1f}

  Next Steps:
    1. Load all 9 CSVs into SQL Server (import wizard or BCP)
    2. Set up SSIS packages to move them to Snowflake RAW schema
    3. Build dbt staging models on top of Snowflake
    4. Run ml_deal_features.sql to create the ML feature table
    5. Start Python EDA and model training
""")