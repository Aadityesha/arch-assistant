from fastapi import FastAPI, UploadFile, File
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import json
import os

app = FastAPI()

# --- CONFIG ---
PROJECT_ID = "arch-assessor-demo"
LOCATION = "us-central1"
BUCKET_NAME = "arch-assessor-rules-v1" 

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-flash")

def load_all_pdfs_from_bucket(bucket_name):
    """Downloads all PDFs from the bucket and prepares them for the model"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    pdf_parts = []
    file_names = []

    print(f"--- Loading Rulebooks from gs://{bucket_name} ---")
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            print(f"Found rulebook: {blob.name}")
            # Download PDF bytes into memory
            pdf_data = blob.download_as_bytes()
            # Create Gemini Part
            pdf_part = Part.from_data(pdf_data, mime_type="application/pdf")
            pdf_parts.append(pdf_part)
            file_names.append(blob.name)
            
    return pdf_parts, file_names

@app.get("/")
def home():
    return {"message": "Architecture Assessor is running!"}

@app.post("/analyze")
async def analyze_architecture(file: UploadFile = File(...)):
    try:
        # 1. Load the User's Diagram
        image_bytes = await file.read()
        image_part = Image.from_bytes(image_bytes)

        # 2. Auto-Load Rules from Cloud Storage
        rule_parts, rule_names = load_all_pdfs_from_bucket(BUCKET_NAME)
        
        if not rule_parts:
            return {"error": "No PDF rulebooks found in the storage bucket!"}

        # 3. Build Prompt
        # We add the image first, then ALL the PDF parts
        prompt = [
            "Role: Solutions Architect Auditor.",
            f"Task: Audit this diagram against the following {len(rule_names)} internal rulebooks: {', '.join(rule_names)}.",
            "Instructions: Cross-reference the visual diagram against ALL attached PDF documents. Identify violations. Assign scores.",
            "Output: JSON only. Format: { \"scores\": {...}, \"violations\": [...] }",
            image_part
        ]
        
        # Extend the prompt with the list of PDF parts
        prompt.extend(rule_parts)

        # 4. Generate
        print("Sending context to Gemini...")
        response = model.generate_content(prompt)
        
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)

    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}