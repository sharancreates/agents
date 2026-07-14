from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import SessionLocal, engine
from api import models
from orchestrator.celery_app import process_submission_task

# Create the database tables automatically on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hackathon Evaluation Pipeline")

# Dependency to yield a database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SubmissionRequest(BaseModel):
    url: str  # GitHub repo URL or ZIP link

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/submissions")
def ingest_submission(submission: SubmissionRequest, db: Session = Depends(get_db)):
    # 1. Persist the new submission record to PostgreSQL
    new_submission = models.Submission(url=submission.url)
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # 2. Trigger the Celery task in the background
    process_submission_task.delay(new_submission.id, new_submission.url)
    
    return {
        "message": "Submission received", 
        "submission_id": new_submission.id,
        "submission_url": new_submission.url,
        "status": "pending"
    }