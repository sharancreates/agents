import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import SessionLocal, engine
from api import models
from api.synthesis_service import calculate_synthesis_score, generate_synthesis_summary, get_default_weights
from api.feedback_service import generate_participant_feedback
from orchestrator.celery_app import process_submission_task

# Create the database tables automatically on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hackathon Evaluation Pipeline")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to yield a database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request schemas
class SubmissionRequest(BaseModel):
    team_name: str
    repo_url: str

class SynthesisRequest(BaseModel):
    code_quality: Optional[float] = 30.0
    functionality: Optional[float] = 30.0
    originality: Optional[float] = 20.0
    innovation: Optional[float] = 20.0

# Seeding Logic
def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.Submission).count() > 0:
            return
        
        # Load from frontend mock data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, "frontend", "src", "mockData", "submissions.json")
        if not os.path.exists(json_path):
            print(f"Seed file not found at: {json_path}")
            return
            
        with open(json_path, "r") as f:
            data = json.load(f)
            
        for item in data:
            submitted_at = item.get("submitted_at")
            if submitted_at:
                # Parse ISO date safely
                try:
                    start_dt = datetime.datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
                except ValueError:
                    start_dt = datetime.datetime.utcnow()
            else:
                start_dt = datetime.datetime.utcnow()
                
            completed_dt = start_dt if item.get("pipeline_status") == "complete" else None
            
            sub = models.Submission(
                submission_id=item.get("submission_id"),
                team_name=item.get("team_name"),
                repo_url=item.get("repo_url"),
                commit_sha=item.get("commit_sha") or str(uuid.uuid4()).replace("-", "")[:40],
                pipeline_status=item.get("pipeline_status", "pending"),
                pipeline_started_at=start_dt,
                pipeline_completed_at=completed_dt,
                overall_score=item.get("overall_score"),
                synthesis_summary=item.get("synthesis_summary"),
                requires_manual_review=False,
                review_status="unreviewed",
                code_quality=item.get("code_quality"),
                functionality=item.get("functionality"),
                originality=item.get("originality"),
                innovation=item.get("innovation"),
                rubric_weights=get_default_weights(),
                participant_feedback=item.get("participant_feedback") or generate_participant_feedback(item)
            )
            db.add(sub)
        db.commit()
        print("Database successfully seeded with submissions.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

# Run seed on import / startup
seed_database()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "orchestrator"}

# Submissions Endpoints
@app.get("/api/submissions")
def get_submissions(db: Session = Depends(get_db)):
    subs = db.query(models.Submission).all()
    # Format database models to match frontend expectations
    result = []
    for s in subs:
        result.append({
            "id": s.id,
            "submission_id": s.submission_id,
            "team_name": s.team_name,
            "repo_url": s.repo_url,
            "commit_sha": s.commit_sha,
            "pipeline_status": s.pipeline_status,
            "submitted_at": s.pipeline_started_at.isoformat() + "Z" if s.pipeline_started_at else None,
            "overall_score": s.overall_score,
            "synthesis_summary": s.synthesis_summary,
            "code_quality": s.code_quality,
            "functionality": s.functionality,
            "originality": s.originality,
            "innovation": s.innovation,
            "participant_feedback": s.participant_feedback
        })
    return result

@app.get("/api/submissions/{submission_id}")
def get_submission_detail(submission_id: str, db: Session = Depends(get_db)):
    s = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    return {
        "id": s.id,
        "submission_id": s.submission_id,
        "team_name": s.team_name,
        "repo_url": s.repo_url,
        "commit_sha": s.commit_sha,
        "pipeline_status": s.pipeline_status,
        "submitted_at": s.pipeline_started_at.isoformat() + "Z" if s.pipeline_started_at else None,
        "overall_score": s.overall_score,
        "synthesis_summary": s.synthesis_summary,
        "code_quality": s.code_quality,
        "functionality": s.functionality,
        "originality": s.originality,
        "innovation": s.innovation,
        "participant_feedback": s.participant_feedback
    }

@app.post("/api/submissions")
def create_submission(request: SubmissionRequest, db: Session = Depends(get_db)):
    sub_id = f"sub_{db.query(models.Submission).count() + 1:03d}"
    commit_sha = str(uuid.uuid4()).replace("-", "")[:40]
    
    # Initialize JSON components with pending state
    pending_dim = {
        "status": "pending",
        "score": None,
        "summary": None,
        "flags": [],
        "started_at": None,
        "completed_at": None
    }
    
    new_submission = models.Submission(
        submission_id=sub_id,
        team_name=request.team_name,
        repo_url=request.repo_url,
        commit_sha=commit_sha,
        pipeline_status="pending",
        pipeline_started_at=datetime.datetime.utcnow(),
        code_quality=pending_dim,
        functionality={**pending_dim, "raw_metrics": {"tests_passed": 0, "total_tests": 0, "avg_runtime_ms": 0, "peak_memory_mb": 0}},
        originality=pending_dim,
        innovation=pending_dim,
        rubric_weights=get_default_weights()
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # Trigger background pipeline execution via Celery
    process_submission_task.delay(new_submission.id, new_submission.repo_url)
    
    return {
        "message": "Submission received", 
        "submission_id": new_submission.submission_id,
        "team_name": new_submission.team_name,
        "repo_url": new_submission.repo_url,
        "status": "pending"
    }

class BulkSynthesisRequest(BaseModel):
    code_quality: float
    functionality: float
    originality: float
    innovation: float

@app.post("/api/submissions/{submission_id}/synthesize")
def run_synthesis(submission_id: str, weights: SynthesisRequest, db: Session = Depends(get_db)):
    s = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    weights_dict = {
        "code_quality": weights.code_quality,
        "functionality": weights.functionality,
        "originality": weights.originality,
        "innovation": weights.innovation
    }
    
    # Extract data dict for synthesis calculations
    sub_data = {
        "team_name": s.team_name,
        "code_quality": s.code_quality,
        "functionality": s.functionality,
        "originality": s.originality,
        "innovation": s.innovation
    }
    
    s.overall_score = calculate_synthesis_score(sub_data, weights_dict)
    s.synthesis_summary = generate_synthesis_summary(sub_data, weights_dict)
    s.rubric_weights = weights_dict
    
    db.commit()
    
    return {
        "submission_id": s.submission_id,
        "overall_score": s.overall_score,
        "synthesis_summary": s.synthesis_summary,
        "rubric_weights": s.rubric_weights
    }

@app.post("/api/submissions/recalculate-all-synthesis")
def recalculate_all_synthesis(weights: BulkSynthesisRequest, db: Session = Depends(get_db)):
    weights_dict = {
        "code_quality": weights.code_quality,
        "functionality": weights.functionality,
        "originality": weights.originality,
        "innovation": weights.innovation
    }
    
    subs = db.query(models.Submission).filter(models.Submission.pipeline_status == "complete").all()
    updated_subs = []
    
    for s in subs:
        sub_data = {
            "team_name": s.team_name,
            "code_quality": s.code_quality,
            "functionality": s.functionality,
            "originality": s.originality,
            "innovation": s.innovation
        }
        s.overall_score = calculate_synthesis_score(sub_data, weights_dict)
        s.synthesis_summary = generate_synthesis_summary(sub_data, weights_dict)
        s.rubric_weights = weights_dict
        updated_subs.append({
            "submission_id": s.submission_id,
            "overall_score": s.overall_score
        })
        
    db.commit()
    return {"message": f"Successfully recalculated {len(updated_subs)} submissions.", "updates": updated_subs}

@app.get("/api/submissions/{submission_id}/feedback")
def get_participant_feedback_endpoint(submission_id: str, db: Session = Depends(get_db)):
    s = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if not s.participant_feedback:
        sub_data = {
            "team_name": s.team_name,
            "code_quality": s.code_quality,
            "functionality": s.functionality,
            "originality": s.originality,
            "innovation": s.innovation
        }
        s.participant_feedback = generate_participant_feedback(sub_data)
        db.commit()
        
    return s.participant_feedback

@app.post("/api/submissions/{submission_id}/feedback")
def generate_feedback_endpoint(submission_id: str, db: Session = Depends(get_db)):
    s = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    sub_data = {
        "team_name": s.team_name,
        "code_quality": s.code_quality,
        "functionality": s.functionality,
        "originality": s.originality,
        "innovation": s.innovation
    }
    s.participant_feedback = generate_participant_feedback(sub_data)
    db.commit()
    return s.participant_feedback