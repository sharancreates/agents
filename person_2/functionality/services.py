import os
from typing import List, Dict, Any
from person_2.functionality.models import TestCaseInput, FunctionalityConfig
from person_2.functionality.runner import DynamicExecutionRunner

def run_background_evaluation_pipeline(
    submission_id: str,
    script_path: str,
    test_cases_raw: List[Dict[str, Any]],
    timeout_seconds: float = 2.0
) -> Dict[str, Any]:
    """
    Unified entry point for background workers (Celery) to execute 
    and parse dynamic submission evaluations.
    """
    # 1. Parse raw dictionary inputs from the task broker into structured Pydantic schemas
    test_cases = [
        TestCaseInput(
            test_id=tc.get("test_id", f"TC_{i}"),
            input_data=tc.get("input_data", ""),
            expected_output=tc.get("expected_output", "")
        )
        for i, tc in enumerate(test_cases_raw)
    ]
    
    config = FunctionalityConfig(timeout_seconds=timeout_seconds)
    
    # 2. Execute the multi-language sandbox run matrix
    report = DynamicExecutionRunner.execute_script(
        script_path=script_path,
        test_cases=test_cases,
        config=config
    )
    
    # 3. Serialize back into a dictionary payload for the database / broker states
    return report.model_dump()