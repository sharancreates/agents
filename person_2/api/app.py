import os
import sys
import uuid
import json
from datetime import datetime
from typing import Dict, Any  # <-- Added missing type hint imports here
from fastapi import FastAPI, HTTPException, status, BackgroundTasks

# Force Python to look in this exact directory for sister files
CURRENT_API_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_API_DIR not in sys.path:
    sys.path.insert(0, CURRENT_API_DIR)

try:
    import schemas
except ImportError:
    from person_2.api import schemas

from person_2.core.aggregator import MetricsAggregator

app = FastAPI(
    title="Code Quality Agent Microservice",
    description="Asynchronous static code evaluation engine for Person 2 modules.",
    version="1.1.0"
)

# In-memory database to store tracking state definitions
task_registry: Dict[str, Dict[str, Any]] = {}

# Ensure an exports directory exists at the root of person_2
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


def background_analysis_worker(task_id: str, target_path: str):
    """
    Executes deep static analysis processing asynchronously inside a background worker thread,
    serializes a permanent export snapshot, and updates registry states.
    """
    task_registry[task_id]["status"] = "PROCESSING"
    
    try:
        # Run our core static engine crawl
        report_data = MetricsAggregator.evaluate_directory(target_path)
        
        # Build the structured API schema format matches
        formatted_response = {
            "status": "success",
            "summary": report_data["summary"],
            "metrics": report_data["metrics"],
            "file_breakdown": report_data["file_breakdown"]
        }
        
        # Save a serialized backup report directly into exports/
        report_filename = f"report_{task_id}.json"
        report_filepath = os.path.join(EXPORTS_DIR, report_filename)
        with open(report_filepath, "w", encoding="utf-8") as f:
            json.dump(formatted_response, f, indent=4)
            
        # Complete task lifecycle updates
        task_registry[task_id].update({
            "status": "COMPLETED",
            "completed_at": datetime.utcnow().isoformat(),
            "report_file": report_filepath,
            "result": formatted_response
        })
        
    except Exception as err:
        task_registry[task_id].update({
            "status": "FAILED",
            "completed_at": datetime.utcnow().isoformat(),
            "result": {"status": "error", "message": str(err)}
        })


@app.post(
    "/api/v1/analyze", 
    response_model=schemas.AnalysisResponse, 
    status_code=status.HTTP_200_OK,
    summary="Analyze Local Codebase Directory (Synchronous)"
)
async def analyze_codebase_sync(payload: schemas.AnalysisRequest):
    target_path = payload.directory_path
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise HTTPException(status_code=404, detail="Target directory resource reference does not exist.")
    
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
    """
    Ingests a system folder path, registers an execution tracking token, 
    queues the core processing job to a background execution sequence, and releases connection handles.
    """
    target_path = payload.directory_path

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Target path does not exist: '{target_path}'")
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail="Target path is not a directory container.")

    task_id = str(uuid.uuid4())
    
    # Initialize state inside registry tracking layout
    task_registry[task_id] = {
        "task_id": task_id,
        "status": "PENDING",
        "directory_path": target_path,
        "completed_at": None,
        "report_file": None,
        "result": None
    }

    # Queue the task method over to FastAPI worker loops
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
    """
    Queries the runtime tracking registry to return structural processing status or final aggregations.
    """
    if task_id not in task_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requested background execution token tracking reference '{task_id}' was not found."
        )
    return task_registry[task_id]