from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Existing schemas remain above ---
class AnalysisRequest(BaseModel):
    directory_path: str = Field(..., description="The absolute filesystem path to the directory targeting analysis.")

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

# --- NEW: Async Subsystem Schemas ---
class AsyncAnalysisResponse(BaseModel):
    status: str = "accepted"
    task_id: str
    message: str
    check_status_url: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    directory_path: str
    completed_at: Optional[str] = None
    report_file: Optional[str] = None
    result: Optional[AnalysisResponse] = None