import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from person_2.functionality.models import TestCaseInput, FunctionalityConfig, FunctionalityReport, ConsolidatedGradeReport
from person_2.functionality.runner import DynamicExecutionRunner
from person_2.functionality.scoring import EvaluationScoringEngine

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluation Agents"])

class FunctionalityEvaluationRequest(BaseModel):
    """The incoming payload structure sent by the central orchestrator."""
    script_path: str
    test_cases: List[TestCaseInput]
    config: Optional[FunctionalityConfig] = FunctionalityConfig()

class CompleteCompositeScoringRequest(BaseModel):
    """Combines execution parameters and parsed static summary inputs."""
    submission_id: str
    script_path: str
    test_cases: List[TestCaseInput]
    static_metrics: Dict[str, Any]
    config: Optional[FunctionalityConfig] = FunctionalityConfig()

@router.post("/run-tests", response_model=FunctionalityReport)
async def evaluate_submission_functionality(request: FunctionalityEvaluationRequest):
    """Triggers isolation run matrix to return pure execution telemetry logs."""
    if not os.path.exists(request.script_path):
        raise HTTPException(status_code=404, detail=f"Script not found at: '{request.script_path}'")
    try:
        return DynamicExecutionRunner.execute_script(request.script_path, request.test_cases, request.config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score-submission", response_model=ConsolidatedGradeReport)
async def evaluate_and_score_submission(request: CompleteCompositeScoringRequest):
    """Executes dynamic verification checks and blends static metrics into a composite report."""
    if not os.path.exists(request.script_path):
        raise HTTPException(status_code=404, detail=f"Script not found at: '{request.script_path}'")
    try:
        # 1. Run dynamic analysis matrix
        func_report = DynamicExecutionRunner.execute_script(request.script_path, request.test_cases, request.config)
        
        # 2. Compute final blended grading weights
        consolidated_report = EvaluationScoringEngine.calculate_composite_grade(
            submission_id=request.submission_id,
            func_report=func_report,
            static_metrics=request.static_metrics
        )
        return consolidated_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))