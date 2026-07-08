import os
import shutil
import uuid
from typing import List, Dict, Any
from person_2.functionality.models import TestCaseInput, FunctionalityConfig
from person_2.functionality.runner import DynamicExecutionRunner

def run_background_evaluation_pipeline(
    submission_id: str,
    script_path: str,
    test_cases_raw: List[Dict[str, Any]],
    timeout_seconds: float = 2.0,
    shared_volume_root: str = "."
) -> Dict[str, Any]:
    """
    Unified entry point for concurrent background workers.
    Safely isolates the target script execution into a uniquely 
    isolated scratch workspace directory to prevent shared-disk cross-talk.
    """
    # 1. Parse raw dict inputs from the central message queue into Pydantic models
    test_cases = [
        TestCaseInput(
            test_id=tc.get("test_id", f"TC_{i}"),
            input_data=tc.get("input_data", ""),
            expected_output=tc.get("expected_output", "")
        )
        for i, tc in enumerate(test_cases_raw)
    ]
    
    config = FunctionalityConfig(timeout_seconds=timeout_seconds)
    
    # 2. Extract script details and build an isolated execution directory path
    if not os.path.isabs(script_path):
        full_script_path = os.path.abspath(os.path.join(shared_volume_root, script_path))
    else:
        full_script_path = script_path

    if not os.path.exists(full_script_path):
        return {
            "status": "SYSTEM_ERROR",
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "success_rate": 0.0,
            "peak_memory_bytes": 0,
            "test_breakdown": [],
            "error_summary": f"ORCHESTRATION_FAILURE: Script not found on shared volume disk: {full_script_path}"
        }

    # Generate a unique directory name for this specific run session
    base_dir, filename = os.path.split(full_script_path)
    unique_run_id = f"run_{submission_id}_{uuid.uuid4().hex[:8]}"
    scratch_workspace = os.path.join(base_dir, unique_run_id)
    os.makedirs(scratch_workspace, exist_ok=True)
    
    isolated_script_path = os.path.join(scratch_workspace, filename)
    
    try:
        # Copy file to the isolated sandbox environment
        shutil.copy2(full_script_path, isolated_script_path)
        
        # 3. Trigger your multi-language performance profiling executor
        report = DynamicExecutionRunner.execute_script(
            script_path=isolated_script_path,
            test_cases=test_cases,
            config=config
        )
        
        result_payload = report.model_dump()
        
    finally:
        # 4. Clean up the isolated directory workspace immediately to prevent disk bloating
        if os.path.exists(scratch_workspace):
            shutil.rmtree(scratch_workspace, ignore_errors=True)
            
    return result_payload