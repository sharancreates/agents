from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TestCaseInput(BaseModel):
    """Defines an individual test case input/output assertion target."""
    test_id: str
    input_data: str  # Arguments or stdin stream data fed to the student's code
    expected_output: str  # The expected target stdout string to validate against

class FunctionalityConfig(BaseModel):
    """Configuration parameters for executing a specific problem statement's test suite."""
    timeout_seconds: float = Field(default=5.0, description="Max execution time before hard termination.")
    memory_limit_mb: Optional[int] = Field(default=256, description="Hardware memory ceiling boundary.")

class TestCaseResult(BaseModel):
    """The granular evaluation telemetry of an individual test case run."""
    test_id: str
    passed: bool
    runtime_ms: float
    observed_output: str
    error_message: Optional[str] = None

class FunctionalityReport(BaseModel):
    """The comprehensive synthesis report outputted by the functionality agent engine."""
    status: str = "COMPLETED"
    total_tests: int
    passed_tests: int
    success_rate: float  # Percentage of passing assertions
    peak_memory_bytes: int
    test_breakdown: List[TestCaseResult]
    error_summary: Optional[str] = None