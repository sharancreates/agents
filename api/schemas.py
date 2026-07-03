from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

# ---------------------------------------------------------
# Enums & Sub-Models
# ---------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class Flag(BaseModel):
    """
    Upgraded from a simple string to support actionable UI components.
    Example: Clicking a plagiarism flag to view the referenced submission.
    """
    type: str
    message: str
    reference_id: Optional[str] = None 

# ---------------------------------------------------------
# Core Dimension Model
# ---------------------------------------------------------

class DimensionResult(BaseModel):
    """
    Tracks the output of an individual agent (e.g., Code Quality, Functionality).
    Fields are Optional so partial updates can be saved while the agent runs.
    """
    status: JobStatus = JobStatus.PENDING
    score: Optional[float] = None
    summary: Optional[str] = None
    flags: List[Flag] = []
    raw_metrics: Dict[str, Any] = {}
    
    # Crucial for UI: If the sandbox crashes, we need to know why without dropping the whole DB record.
    error_message: Optional[str] = None 

# ---------------------------------------------------------
# Main Evaluation Record
# ---------------------------------------------------------

class EvaluationResult(BaseModel):
    submission_id: str
    
    # UI Metadata: Optional in case P1 prefers to join this from a separate PostgreSQL table, 
    # but highly recommended here for a flat, fast JSON response to the frontend.
    team_name: Optional[str] = None
    repo_url: Optional[str] = None
    
    # Global Pipeline State
    pipeline_status: JobStatus = JobStatus.PENDING
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Core dimensions populated by different agents as they complete async jobs
    code_quality: Optional[DimensionResult] = None
    functionality: Optional[DimensionResult] = None
    originality: Optional[DimensionResult] = None
    innovation: Optional[DimensionResult] = None
    
    # Final synthesized output (Calculated by the Synthesis Agent)
    overall_score: Optional[float] = None