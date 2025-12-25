from google.cloud import bigquery
import os

# Setup
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.popen("gcloud config get-value project").read().strip()
client = bigquery.Client(project=project_id)

# Query
query = f"""
    SELECT timestamp, image_filename, overall_score 
    FROM `{project_id}.arch_assessor_logs.audit_history`
    ORDER BY timestamp DESC
    LIMIT 1
"""

try:
    print(f"🔍 Checking Audit Log for project: {project_id}...")
    query_job = client.query(query)
    results = list(query_job)

    if results:
        for row in results:
            print("\n✅ SUCCESS! LOG ENTRY FOUND:")
            print(f"   • Time: {row.timestamp}")
            print(f"   • File: {row.image_filename}")
            print(f"   • Score: {row.overall_score}")
    else:
        print("\n⚠️ No logs found yet. (Did the Curl command finish?)")

except Exception as e:
    print(f"\n❌ Error: {e}")
