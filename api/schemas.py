from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DimensionResult(BaseModel):
    score: float
    summary: str
    flags: List[str] = []
    raw_metrics: Dict[str, Any] = {}

class EvaluationResult(BaseModel):
    submission_id: int
    
    # Core dimensions populated by different agents
    code_quality: Optional[DimensionResult] = None
    functionality: Optional[DimensionResult] = None
    originality: Optional[DimensionResult] = None
    innovation: Optional[DimensionResult] = None
    
    # Final synthesized output
    overall_score: Optional[float] = None