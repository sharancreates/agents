from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import os

# Import the functionality agent core components you just built
from person_2.functionality.models import TestCaseInput, FunctionalityConfig, FunctionalityReport
from person_2.functionality.runner import DynamicExecutionRunner

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluation Agents"])

class FunctionalityEvaluationRequest(BaseModel):
    """The incoming payload structure sent by Person 1's global orchestrator."""
    script_path: str
    test_cases: List[TestCaseInput]
    config: Optional[FunctionalityConfig] = FunctionalityConfig()

@router.post("/run-tests", response_model=FunctionalityReport)
async def evaluate_submission_functionality(request: FunctionalityEvaluationRequest):
    """
    Triggers the Dynamic Execution Sandbox Runner.
    Executes code matching the extension type, enforces hard timeouts, 
    and profiles peak RAM / runtime metrics.
    """
    # 1. Sanity check: Ensure the requested workspace script file exists on disk
    if not os.path.exists(request.script_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Target execution script not found at path: '{request.script_path}'"
        )
        
    try:
        # 2. Delegate the task to your multi-language strategy execution engine
        report = DynamicExecutionRunner.execute_script(
            script_path=request.script_path,
            test_cases=request.test_cases,
            config=request.config
        )
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Sandboxing Failure during processing execution: {str(e)}"
        )