from google.cloud import bigquery
import os

# Get Project ID
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.popen("gcloud config get-value project").read().strip()
client = bigquery.Client(project=project_id)

# 1. Create Dataset
dataset_id = f"{project_id}.arch_assessor_logs"
dataset = bigquery.Dataset(dataset_id)
dataset.location = "us-central1"
try:
    client.create_dataset(dataset, timeout=30)
    print(f"✅ Created dataset: {dataset_id}")
except Exception:
    print(f"✅ Dataset already exists")

# 2. Create Table
table_id = f"{dataset_id}.audit_history"
schema = [
    bigquery.SchemaField("request_id", "STRING"),
    bigquery.SchemaField("timestamp", "TIMESTAMP"),
    bigquery.SchemaField("image_filename", "STRING"),
    bigquery.SchemaField("overall_score", "INTEGER"),
    bigquery.SchemaField("violations_count", "INTEGER"),
    bigquery.SchemaField("raw_response", "STRING"),
]
table = bigquery.Table(table_id, schema=schema)
try:
    client.create_table(table)
    print(f"✅ Created table: {table_id}")
except Exception:
    print(f"✅ Table already exists")
