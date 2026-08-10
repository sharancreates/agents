from pydantic import BaseModel
from typing import List, Optional

class TestCaseInput(BaseModel):
    """The input payload signature representing a target test parameter evaluation block."""
    test_id: str
    input_data: str
    expected_output: str

class FunctionalityConfig(BaseModel):
    """Execution constraints configuration profile."""
    timeout_seconds: float = 2.0
    memory_limit_mb: int = 256

class TestCaseResult(BaseModel):
    """Evaluation result for an individual operational unit execution pass."""
    test_id: str
    passed: bool
    runtime_ms: float
    observed_output: str
    error_message: Optional[str] = None

class FunctionalityReport(BaseModel):
    """The unified data structure returned after running a complete test matrix."""
    status: str = "COMPLETED"
    total_tests: int
    passed_tests: int
    success_rate: float
    peak_memory_bytes: int
    test_breakdown: List[TestCaseResult]
    error_summary: Optional[str] = None

class ConsolidatedGradeReport(BaseModel):
    """The final composite evaluation profile combining dynamic behavioral vectors and static parameters."""
    submission_id: str
    functionality_score: float  # Driven by unit test success_rate (0-100)
    efficiency_score: float     # Penalty-adjusted resource and timeout score (0-100)
    code_quality_score: float   # Driven by static code smell counts (0-100)
    final_weighted_grade: float # Computed final grade scale (0.0 to 10.0)
    verdict: str                # Standardized system verdict mapping string