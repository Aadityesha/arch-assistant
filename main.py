from fastapi import FastAPI, UploadFile, File
from google.cloud import storage, bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import json
import uuid
import datetime
import os

app = FastAPI()

# CONFIG (Auto-detects project ID)
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = "edp-rulebooks-library"
BQ_TABLE_ID = f"{PROJECT_ID}.arch_assessor_logs.audit_history"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-flash")
bq_client = bigquery.Client()

@app.get("/")
def health_check():
    return {"status": "alive", "system": "enterprise-v2-automated"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    req_id = str(uuid.uuid4())
    try:
        # 1. Read Image
        img_data = await file.read()
        image_part = Image.from_bytes(img_data)
        
        # 2. Load Rules
        storage_client = storage.Client()
        blobs = storage_client.bucket(BUCKET_NAME).list_blobs()
        rules = [Part.from_data(b.download_as_bytes(), mime_type="application/pdf") for b in blobs if b.name.endswith(".pdf")]

        # 3. Generate
        prompt = ["Role: Enterprise Architect. Output JSON.", image_part] + rules
        response = model.generate_content(prompt)
        result = json.loads(response.text.replace('```json', '').replace('```', ''))

        # 4. Log to BigQuery
        row = {
            "request_id": req_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "image_filename": file.filename,
            "overall_score": result.get("scores", {}).get("actual_violation_score", 0),
            "violations_count": len(result.get("violations", [])),
            "raw_response": json.dumps(result)
        }
        bq_client.insert_rows_json(BQ_TABLE_ID, [row])
        
        return result
    except Exception as e:
        return {"error": str(e)}