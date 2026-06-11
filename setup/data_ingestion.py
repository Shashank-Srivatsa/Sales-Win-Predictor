#!/usr/bin/env python3
"""
Sales Win Predictor - Automated Data Ingestion to Snowflake

This script automates the process of:
1. Uploading CSV files to Snowflake stage
2. Creating tables (if not exist)
3. Copying data into tables

Prerequisites:
- Python 3.8+
- Dependencies: pip install -r requirements.txt
- Snowflake account with appropriate permissions
- .env file configured with Snowflake credentials
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Import Snowflake connector
try:
    import snowflake.connector
except ImportError:
    print("Error: snowflake-connector-python not installed")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_snowflake_connection():
    """Create and return Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'sales_win_predictor'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'raw_crm_data')
        )
        logger.info("✓ Connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"✗ Failed to connect to Snowflake: {e}")
        sys.exit(1)

def setup_database_schema(conn):
    """Create database and schema if they don't exist."""
    cursor = conn.cursor()
    try:
        database = os.getenv('SNOWFLAKE_DATABASE', 'sales_win_predictor')
        schema = os.getenv('SNOWFLAKE_SCHEMA', 'raw_crm_data')

        logger.info(f"Setting up database: {database}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE DATABASE {database}")

        logger.info(f"Setting up schema: {schema}")
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        cursor.execute(f"USE SCHEMA {schema}")

        logger.info("✓ Database and schema ready")
    except Exception as e:
        logger.error(f"✗ Failed to setup database/schema: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def create_stage_and_format(conn):
    """Create stage and CSV file format."""
    cursor = conn.cursor()
    try:
        logger.info("Creating stage: crm_stage")
        cursor.execute("""
            CREATE OR REPLACE STAGE crm_stage
            COMMENT = 'Stage for uploading CRM CSV files'
        """)

        logger.info("Creating CSV file format")
        cursor.execute("""
            CREATE OR REPLACE FILE FORMAT csv_format
            TYPE = 'CSV'
            COMPRESSION = 'GZIP'
            FIELD_DELIMITER = ','
            RECORD_DELIMITER = '\\n'
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('NULL', '')
            ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
        """)

        logger.info("✓ Stage and format created")
    except Exception as e:
        logger.error(f"✗ Failed to create stage/format: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def upload_csv_files(conn, data_folder):
    """Upload all CSV files to Snowflake stage."""
    cursor = conn.cursor()
    csv_files = list(Path(data_folder).glob("*.csv"))

    if not csv_files:
        logger.warning(f"⚠ No CSV files found in {data_folder}")
        return

    logger.info(f"Found {len(csv_files)} CSV files to upload")

    try:
        for csv_file in csv_files:
            logger.info(f"Uploading: {csv_file.name}")
            # Use forward slashes for Snowflake path
            file_path = str(csv_file).replace('\\', '/')
            cursor.execute(f"PUT file://{file_path} @crm_stage AUTO_COMPRESS=TRUE")
            logger.info(f"✓ Uploaded: {csv_file.name}")
    except Exception as e:
        logger.error(f"✗ Failed to upload CSV files: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def create_tables_and_load_data(conn):
    """Create tables and load data from staged CSV files."""
    cursor = conn.cursor()

    # Table definitions (simplified, without foreign keys)
    tables = {
        'crm_accounts': """
            CREATE OR REPLACE TABLE crm_accounts (
                account_id VARCHAR(50) NOT NULL PRIMARY KEY,
                account_name VARCHAR(255),
                industry VARCHAR(100),
                country VARCHAR(100),
                region VARCHAR(100),
                annual_revenue_band VARCHAR(100),
                account_type VARCHAR(100),
                account_tier INTEGER,
                number_of_employees INTEGER,
                is_active INTEGER,
                created_date DATE,
                last_activity_date DATE
            )
        """,
        'crm_users': """
            CREATE OR REPLACE TABLE crm_users (
                user_id VARCHAR(50) NOT NULL PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255),
                role VARCHAR(100),
                division VARCHAR(100),
                region VARCHAR(100),
                seniority_level VARCHAR(100),
                hire_date DATE,
                is_active INTEGER,
                manager_id VARCHAR(50),
                target_deals_per_year INTEGER
            )
        """,
        'crm_products': """
            CREATE OR REPLACE TABLE crm_products (
                product_id VARCHAR(50) NOT NULL PRIMARY KEY,
                product_name VARCHAR(255),
                product_category VARCHAR(100),
                division VARCHAR(100),
                standard_unit_price DECIMAL(18, 2),
                unit_type VARCHAR(50),
                price_range_low DECIMAL(18, 2),
                price_range_high DECIMAL(18, 2),
                is_active INTEGER,
                created_date DATE
            )
        """,
        'crm_contacts': """
            CREATE OR REPLACE TABLE crm_contacts (
                contact_id VARCHAR(50) NOT NULL PRIMARY KEY,
                account_id VARCHAR(50),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255),
                job_title VARCHAR(100),
                department VARCHAR(100),
                is_primary_contact INTEGER,
                is_decision_maker INTEGER,
                created_date DATE,
                is_active INTEGER
            )
        """,
        'crm_opportunities': """
            CREATE OR REPLACE TABLE crm_opportunities (
                opportunity_id VARCHAR(50) NOT NULL PRIMARY KEY,
                opportunity_name VARCHAR(255),
                account_id VARCHAR(50),
                primary_contact_id VARCHAR(50),
                owner_user_id VARCHAR(50),
                division VARCHAR(100),
                region VARCHAR(100),
                deal_type VARCHAR(100),
                lead_source VARCHAR(100),
                stage VARCHAR(100),
                amount DECIMAL(18, 2),
                discount_pct DECIMAL(5, 2),
                probability_manual DECIMAL(5, 2),
                created_date DATE,
                expected_close_date DATE,
                close_date_actual DATE,
                is_won INTEGER,
                lost_reason VARCHAR(255),
                is_renewal INTEGER,
                fiscal_year INTEGER,
                fiscal_quarter INTEGER,
                is_open INTEGER
            )
        """,
        'crm_activities': """
            CREATE OR REPLACE TABLE crm_activities (
                activity_id VARCHAR(50) NOT NULL PRIMARY KEY,
                opportunity_id VARCHAR(50),
                user_id VARCHAR(50),
                activity_type VARCHAR(100),
                subject VARCHAR(500),
                activity_date DATE,
                duration_minutes INTEGER,
                outcome VARCHAR(100),
                is_outbound INTEGER,
                days_since_deal_created INTEGER
            )
        """,
        'crm_contracts': """
            CREATE OR REPLACE TABLE crm_contracts (
                contract_id VARCHAR(50) NOT NULL PRIMARY KEY,
                opportunity_id VARCHAR(50),
                account_id VARCHAR(50),
                contract_start_date DATE,
                contract_end_date DATE,
                contract_duration_months INTEGER,
                contract_value DECIMAL(18, 2),
                payment_terms VARCHAR(100),
                signed_date DATE,
                contract_status VARCHAR(100),
                has_royalty_clause INTEGER,
                royalty_pct DECIMAL(5, 2),
                royalty_threshold_usd DECIMAL(18, 2),
                number_of_revisions INTEGER
            )
        """,
        'crm_opportunity_line_items': """
            CREATE OR REPLACE TABLE crm_opportunity_line_items (
                line_item_id VARCHAR(50) NOT NULL PRIMARY KEY,
                opportunity_id VARCHAR(50),
                product_id VARCHAR(50),
                line_item_name VARCHAR(255),
                line_item_type VARCHAR(100),
                unit_type VARCHAR(50),
                unit_price DECIMAL(18, 2),
                quantity INTEGER,
                gross_amount DECIMAL(18, 2),
                discount_applied_pct DECIMAL(5, 2),
                net_amount DECIMAL(18, 2),
                is_negotiated INTEGER,
                created_date DATE
            )
        """,
        'crm_opportunity_stage_history': """
            CREATE OR REPLACE TABLE crm_opportunity_stage_history (
                stage_history_id VARCHAR(50) NOT NULL PRIMARY KEY,
                opportunity_id VARCHAR(50),
                from_stage VARCHAR(100),
                to_stage VARCHAR(100),
                stage_entered_date DATE,
                stage_exited_date DATE,
                days_in_stage INTEGER,
                changed_by_user_id VARCHAR(50),
                is_regression INTEGER
            )
        """
    }

    try:
        # Create tables
        for table_name, create_sql in tables.items():
            logger.info(f"Creating table: {table_name}")
            cursor.execute(create_sql)

        # Load data
        for table_name in tables.keys():
            csv_file = f"{table_name}.csv.gz"
            logger.info(f"Loading data into: {table_name}")

            cursor.execute(f"""
                COPY INTO {table_name}
                FROM @crm_stage/{csv_file}
                FILE_FORMAT = (
                    FORMAT_NAME = 'csv_format'
                    PARSE_HEADER = TRUE
                )
                MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            """)

            # Get row count
            result = cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()
            row_count = result[0] if result else 0
            logger.info(f"✓ {table_name}: {row_count} rows loaded")

        logger.info("\n" + "="*60)
        logger.info("✓ ALL DATA LOADED SUCCESSFULLY")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"✗ Failed to create tables/load data: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Sales Win Predictor - Data Ingestion")
    logger.info("="*60)

    # Get data folder path
    data_folder = os.path.join(os.path.dirname(__file__), '..', 'Data')
    data_folder = os.path.abspath(data_folder)

    if not os.path.exists(data_folder):
        logger.error(f"✗ Data folder not found: {data_folder}")
        sys.exit(1)

    # Connect to Snowflake
    conn = get_snowflake_connection()

    try:
        # Setup database and schema
        setup_database_schema(conn)

        # Create stage and file format
        create_stage_and_format(conn)

        # Upload CSV files
        upload_csv_files(conn, data_folder)

        # Create tables and load data
        create_tables_and_load_data(conn)

    finally:
        conn.close()
        logger.info("✓ Connection closed")

if __name__ == '__main__':
    main()
