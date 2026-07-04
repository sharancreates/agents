import os
from fastapi import FastAPI, HTTPException, status
# Standard absolute package tracking
from person_2.api.schemas import AnalysisRequest, AnalysisResponse
from person_2.core.aggregator import MetricsAggregator

app = FastAPI(
    title="Code Quality Agent Microservice",
    description="Isolated static code evaluation engine for Person 2 modules.",
    version="1.0.0"
)

@app.post(
    "/api/v1/analyze", 
    response_model=AnalysisResponse, 
    status_code=status.HTTP_200_OK,
    summary="Analyze Local Codebase Directory"
)
async def analyze_codebase(payload: AnalysisRequest):
    target_path = payload.directory_path

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target directory path structural resource reference does not exist: '{target_path}'"
        )

    if not os.path.isdir(target_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provided target location reference path is not a directory container: '{target_path}'"
        )

    try:
        report_data = MetricsAggregator.evaluate_directory(target_path)
        return {
            "status": "success",
            "summary": report_data["summary"],
            "metrics": report_data["metrics"],
            "file_breakdown": report_data["file_breakdown"]
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Static analysis engine experienced an unexpected collection fault: {str(err)}"
        )