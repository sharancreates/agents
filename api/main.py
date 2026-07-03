from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Hackathon Evaluation Pipeline")

class SubmissionRequest(BaseModel):
    url: str  # GitHub repo URL or ZIP link

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/submissions")
def ingest_submission(submission: SubmissionRequest):
    # TODO: Clone/extract repo, detect language, persist to PostgreSQL
    # TODO: Trigger Celery tasks for P2 and P3 agents
    return {
        "message": "Submission received", 
        "submission_url": submission.url,
        "status": "pending"
    }