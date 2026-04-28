import snowflake.connector
import os

conn = snowflake.connector.connect(
    user='SHASHANKSRIVATSA423',
    password='DataWithBara@2025',
    account='QACMQHK-SN72200',
    warehouse='COMPUTE_WH',
    database='SALES_WIN_DB',
    schema='BRONZE'
)

cursor = conn.cursor()

# Create stage
cursor.execute("CREATE OR REPLACE STAGE crm_stage")

folder_path = r"C:\Users\shash\OneDrive\Documents\Sales-Win-Predictor\Data"

for file in os.listdir(folder_path):
    if file.endswith(".csv"):
        file_path = os.path.join(folder_path, file)

        cursor.execute(f"PUT file://{file_path} @crm_stage AUTO_COMPRESS=TRUE")

        table_name = file.replace(".csv", "")
        stage_file = file + ".gz"

        cursor.execute(f"""
        CREATE OR REPLACE TABLE {table_name}
        USING TEMPLATE (
        SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
        FROM TABLE(
        INFER_SCHEMA(
            LOCATION =>'@crm_stage/{stage_file}',
            FILE_FORMAT =>'csv_format'
        )
    )
)
""")

        cursor.execute(f"""
        COPY INTO {table_name}
        FROM @crm_stage/{stage_file}
        FILE_FORMAT = (FORMAT_NAME = 'csv_format')
        """)

print("Done loading all CSVs into Snowflake.")