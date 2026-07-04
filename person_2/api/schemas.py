from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AnalysisRequest(BaseModel):
    directory_path: str = Field(
        ..., 
        description="The absolute filesystem path to the directory targeting analysis.",
        example="C:\\Users\\Rudra\\OneDrive\\Desktop\\Agent\\agents"
    )

class FileBreakdownItem(BaseModel):
    file_path: str
    language: str
    cyclomatic_complexity: int
    issues_found: int
    smells: List[Dict[str, Any]]

class SummaryMetrics(BaseModel):
    total_files_evaluated: int
    overall_maintainability_rating: str
    global_issue_count: int

class ComplexityMetrics(BaseModel):
    average_cyclomatic_complexity: float
    max_complexity_observed: int

class AnalysisResponse(BaseModel):
    status: str = "success"
    summary: SummaryMetrics
    metrics: ComplexityMetrics
    file_breakdown: List[FileBreakdownItem]