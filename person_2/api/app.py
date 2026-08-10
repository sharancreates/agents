import os
import sys
import uuid
import json
from datetime import datetime, UTC
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status, BackgroundTasks

# Force Python to check this exact folder for sister files
CURRENT_API_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_API_DIR not in sys.path:
    sys.path.insert(0, CURRENT_API_DIR)

try:
    import schemas
    from database import SessionLocal, TaskModel, init_db
except ImportError:
    from person_2.api import schemas
    from person_2.api.database import SessionLocal, TaskModel, init_db

from person_2.core.aggregator import MetricsAggregator

# Initialize the SQLite tables on startup automatically
init_db()

app = FastAPI(
    title="Code Quality Agent Microservice",
    description="Persistent database-backed static code evaluation engine for Person 2.",
    version="1.2.0"
)

# Ensure an exports directory exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


def background_analysis_worker(task_id: str, target_path: str):
    """
    Executes code evaluation on a worker thread, updates records, 
    and saves serialized payloads permanently to disk.
    """
    db = SessionLocal()
    try:
        # 1. Update task status to PROCESSING in DB
        db_task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
        if db_task:
            db_task.status = "PROCESSING"
            db.commit()

        # 2. Run the heavy analysis crawl
        report_data = MetricsAggregator.evaluate_directory(target_path)
        
        formatted_response = {
          "status": "success",
          "summary": report_data["summary"],
          "metrics": report_data["metrics"],
          "file_breakdown": report_data["file_breakdown"]
        }
        
        # 3. Save report to exports folder
        report_filename = f"report_{task_id}.json"
        report_filepath = os.path.join(EXPORTS_DIR, report_filename)
        with open(report_filepath, "w", encoding="utf-8") as f:
            json.dump(formatted_response, f, indent=4)
            
        # 4. Finalize the record entry tracking state
        if db_task:
            db_task.status = "COMPLETED"
            db_task.completed_at = datetime.now(UTC)
            db_task.report_file = report_filepath
            db.commit()
            
    except Exception as err:
        if db_task:
            db_task.status = "FAILED"
            db_task.completed_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


@app.post(
    "/api/v1/analyze", 
    response_model=schemas.AnalysisResponse, 
    status_code=status.HTTP_200_OK,
    summary="Analyze Local Codebase Directory (Synchronous)"
)
async def analyze_codebase_sync(payload: schemas.AnalysisRequest):
    target_path = payload.directory_path
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise HTTPException(status_code=404, detail="Target directory reference does not exist.")
    try:
        report_data = MetricsAggregator.evaluate_directory(target_path)
        return {
            "status": "success",
            "summary": report_data["summary"],
            "metrics": report_data["metrics"],
            "file_breakdown": report_data["file_breakdown"]
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post(
    "/api/v1/analyze/async", 
    response_model=schemas.AsyncAnalysisResponse, 
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze Local Codebase Directory (Asynchronous)"
)
async def analyze_codebase_async(payload: schemas.AnalysisRequest, background_tasks: BackgroundTasks):
    target_path = payload.directory_path

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Target path does not exist: '{target_path}'")
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail="Target path is not a directory container.")

    task_id = str(uuid.uuid4())
    
    # Write initial record entry directly into the persistent DB
    db = SessionLocal()
    try:
        new_task = TaskModel(task_id=task_id, status="PENDING", directory_path=target_path)
        db.add(new_task)
        db.commit()
    finally:
        db.close()

    # Hand off to async thread pools
    background_tasks.add_task(background_analysis_worker, task_id, target_path)

    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "Analysis job accepted successfully and shifted to background processing chains.",
        "check_status_url": f"/api/v1/tasks/{task_id}"
    }


@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=schemas.TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch Background Task Lifecycle Status"
)
async def get_task_status(task_id: str):
    """Queries SQLite directly to fetch the complete tracking history."""
    db = SessionLocal()
    try:
        task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Requested background task token was not found.")
        
        # Read file results if execution finished
        result_payload = None
        if task.status == "COMPLETED" and task.report_file and os.path.exists(task.report_file):
            with open(task.report_file, "r", encoding="utf-8") as f:
                result_payload = json.load(f)

        return {
            "task_id": task.task_id,
            "status": task.status,
            "directory_path": task.directory_path,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "report_file": task.report_file,
            "result": result_payload
        }
    finally:
        db.close()