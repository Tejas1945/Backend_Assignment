from fastapi import FastAPI, UploadFile, File, HTTPException
from .models import Offer, Lead, LeadScore
from .scoring import score_lead
import pandas as pd
import io
from typing import List

app = FastAPI(title="Lead Scoring API")

# In-memory storage
db = {
    "offer": None,
    "leads": [],
    "scores": []
}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Lead Scoring API"}

@app.post("/offer", status_code=201)
def create_offer(offer: Offer):
    """
    Accepts JSON with product/offer details.
    """
    db["offer"] = offer
    return {"message": "Offer created successfully", "offer": offer}

@app.post("/leads/upload", status_code=201)
async def upload_leads(file: UploadFile = File(...)):
    """
    Accepts a CSV file with lead data.
    """
    if file.content_type != 'text/csv':
        raise HTTPException(400, detail="Invalid file type. Please upload a CSV.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        # Basic validation for required columns
        required_columns = {"name", "role", "company", "industry", "location", "linkedin_bio"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(400, detail=f"CSV must contain the following columns: {required_columns}")
        
        leads = df.to_dict(orient='records')
        db["leads"] = [Lead(**lead) for lead in leads]
        # Clear previous scores when new leads are uploaded
        db["scores"] = []
        return {"message": f"{len(db['leads'])} leads uploaded successfully."}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to process CSV file: {e}")

@app.post("/score", status_code=200)
def run_scoring():
    """
    Runs the scoring pipeline on the uploaded leads.
    """
    if not db["offer"]:
        raise HTTPException(400, detail="Offer information is not set. Please POST to /offer first.")
    if not db["leads"]:
        raise HTTPException(400, detail="No leads have been uploaded. Please POST to /leads/upload first.")

    db["scores"] = [score_lead(lead, db["offer"]) for lead in db["leads"]]
    
    return {"message": f"Scoring complete for {len(db['scores'])} leads."}

@app.get("/results", response_model=List[LeadScore])
def get_results():
    """
    Returns the scoring results.
    """
    if not db["scores"]:
        raise HTTPException(404, detail="No scoring results found. Please run scoring via POST to /score.")
    
    return db["scores"]
