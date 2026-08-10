from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class MetricDetail(BaseModel):
    score: float = Field(..., description="Normalized metric evaluation score from 0.0 to 100.0")
    raw_metrics: Dict[str, Any] = Field(default_factory=dict, description="Raw structural counters and metrics")
    flags: List[Dict[str, Any]] = Field(default_factory=list, description="Specific warnings, lint alerts, or smell definitions")
    summary: str = Field(..., description="Human-readable breakdown summarizing this category")

class CodeQualityResult(BaseModel):
    language: str = Field(..., description="Identified programming language of the codebase")
    code_quality: MetricDetail = Field(..., description="Structural metrics covering complexity and styling standards")
    security: Optional[MetricDetail] = Field(None, description="Security vulnerability metrics if checked")