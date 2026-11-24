from pydantic import BaseModel, Field
from typing import List, Optional

class TestCaseInput(BaseModel):
    """The input payload signature representing a target test parameter evaluation block."""
    test_id: str = "TC1"
    input_data: str = ""
    expected_output: str = ""

# Silence Pytest collection warning
TestCaseInput.__test__ = False

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

# Silence Pytest collection warning
TestCaseResult.__test__ = False

class FunctionalityReport(BaseModel):
    """The unified data structure returned after running a complete test matrix."""
    status: str = "COMPLETED"
    total_tests: int
    passed_tests: int
    success_rate: float
    peak_memory_bytes: int
    test_breakdown: List[TestCaseResult]
    error_summary: Optional[str] = None

    @property
    def passed_count(self) -> int:
        return self.passed_tests

    @property
    def total_count(self) -> int:
        return self.total_tests

    @property
    def total_duration_ms(self) -> float:
        return sum(tc.runtime_ms for tc in self.test_breakdown)

    @property
    def peak_memory_mb(self) -> float:
        return round(self.peak_memory_bytes / (1024 * 1024), 2)

class ConsolidatedGradeReport(BaseModel):
    """The final composite evaluation profile combining dynamic behavioral vectors and static parameters."""
    submission_id: str
    functionality_score: float  # Driven by unit test success_rate (0-100)
    efficiency_score: float     # Penalty-adjusted resource and timeout score (0-100)
    code_quality_score: float   # Driven by static code smell counts (0-100)
    final_weighted_grade: float # Computed final grade scale (0.0 to 10.0)
    verdict: str                # Standardized system verdict mapping string
    flags: List[str] = Field(default_factory=list, description="Operational & security alert flags.")
    score_20: float = 0.0       # Grade normalized on a 0-20 scale for composite rubrics
