import os
import pytest
import sys
from fastapi.testclient import TestClient

from person_2.functionality.models import TestCaseInput, FunctionalityConfig, TestCaseResult, FunctionalityReport
from person_2.functionality.runner import DynamicExecutionRunner
from person_2.functionality.services import run_background_evaluation_pipeline
from person_2.functionality.scoring import EvaluationScoringEngine
from person_2.main import app

# Silence Pytest collection warning flags for Pydantic schema models
TestCaseInput.__test__ = False
TestCaseResult.__test__ = False

# Initialize the automated FastAPI mock network test framework on the full app
client = TestClient(app)

@pytest.fixture
def target_scripts(tmpdir):
    """Generates temporary problem submissions with explicit behaviors for evaluation."""
    # 1. A clean passing script processing stdin and returning standard out logs
    passing_script = tmpdir.join("passing_calc.py")
    passing_script.write("import sys\ndata = sys.stdin.read().strip()\nprint(f'PROCESSED:{data}')\n")

    # 2. A script that crashes during evaluation with a runtime exception
    crashing_script = tmpdir.join("crash_script.py")
    crashing_script.write("import sys\nraise ValueError('Simulated compilation or calculation crash')\n")

    # 3. An adversarial script looping forever to test execution boundaries
    infinite_script = tmpdir.join("infinite_loop.py")
    infinite_script.write("import time\nwhile True:\n    time.sleep(0.1)\n")

    return {
        "passing": str(passing_script),
        "crashing": str(crashing_script),
        "infinite": str(infinite_script)
    }

def test_successful_test_case_execution(target_scripts):
    """Asserts that clean logic matching expected outputs passes successfully."""
    test_cases = [
        TestCaseInput(test_id="TC1", input_data="hello", expected_output="PROCESSED:hello"),
        TestCaseInput(test_id="TC2", input_data="world", expected_output="PROCESSED:world")
    ]
    config = FunctionalityConfig(timeout_seconds=2.0)
    
    report = DynamicExecutionRunner.execute_script(target_scripts["passing"], test_cases, config)
    
    assert report.total_tests == 2
    assert report.passed_tests == 2
    assert report.success_rate == 100.0
    assert report.test_breakdown[0].passed is True

def test_failed_assertion_handling(target_scripts):
    """Asserts that code running cleanly but outputting mismatched strings fails explicitly."""
    test_cases = [
        TestCaseInput(test_id="TC3", input_data="mismatch", expected_output="WRONG_TARGET_OUTPUT")
    ]
    config = FunctionalityConfig(timeout_seconds=2.0)
    
    report = DynamicExecutionRunner.execute_script(target_scripts["passing"], test_cases, config)
    
    assert report.passed_tests == 0
    assert report.success_rate == 0.0

def test_runtime_exception_handling(target_scripts):
    """Asserts that code crashes capture standard error messages correctly."""
    test_cases = [
        TestCaseInput(test_id="TC4", input_data="data", expected_output="ANY")
    ]
    config = FunctionalityConfig(timeout_seconds=2.0)
    
    report = DynamicExecutionRunner.execute_script(target_scripts["crashing"], test_cases, config)
    
    assert report.passed_tests == 0
    assert "ValueError" in report.test_breakdown[0].error_message

def test_infinite_loop_timeout_protection(target_scripts):
    """Asserts that scripts stuck in infinite loops are forcefully terminated by timeout constraints."""
    test_cases = [
        TestCaseInput(test_id="TC5", input_data="loop", expected_output="ANY")
    ]
    config = FunctionalityConfig(timeout_seconds=0.5)
    
    report = DynamicExecutionRunner.execute_script(target_scripts["infinite"], test_cases, config)
    
    assert report.passed_tests == 0
    assert "TIMEOUT_FAILURE" in report.test_breakdown[0].error_message

def test_api_endpoint_run_tests(target_scripts):
    """Verifies that the HTTP POST router accepts payloads and marshals returns correctly."""
    payload = {
        "script_path": target_scripts["passing"],
        "test_cases": [
            {"test_id": "API_TC1", "input_data": "fastapi_test", "expected_output": "PROCESSED:fastapi_test"}
        ],
        "config": {"timeout_seconds": 2.0, "memory_limit_mb": 128}
    }
    
    response = client.post("/v1/evaluation/run-tests", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["total_tests"] == 1
    assert data["passed_tests"] == 1
    assert data["test_breakdown"][0]["passed"] is True

def test_background_evaluation_pipeline_service(target_scripts):
    """Verifies that the background worker service correctly consumes raw dicts and returns serialized results."""
    raw_test_cases = [
        {
            "test_id": "BG_TC1",
            "input_data": "service_pipeline_test",
            "expected_output": "PROCESSED:service_pipeline_test"
        }
    ]
    
    result_dict = run_background_evaluation_pipeline(
        submission_id="sub_abc123",
        script_path=target_scripts["passing"],
        test_cases_raw=raw_test_cases,
        timeout_seconds=2.0
    )
    
    assert isinstance(result_dict, dict)
    assert result_dict["status"] == "COMPLETED"
    assert result_dict["total_tests"] == 1
    assert result_dict["passed_tests"] == 1
    assert result_dict["test_breakdown"][0]["test_id"] == "BG_TC1"
    assert result_dict["test_breakdown"][0]["passed"] is True

def test_composite_scoring_aggregation():
    """Verifies that the grading engine properly weighs static and dynamic inputs to output a verdict."""
    mock_func_report = FunctionalityReport(
        total_tests=1,
        passed_tests=1,
        success_rate=100.0,
        peak_memory_bytes=4194304,  # 4MB (Well within limits)
        test_breakdown=[
            TestCaseResult(test_id="T1", passed=True, runtime_ms=12.5, observed_output="OK", error_message=None)
        ]
    )
    
    mock_static_metrics = {
        "smell_count": 2,
        "cyclomatic_complexity": 3
    }
    
    report = EvaluationScoringEngine.calculate_composite_grade(
        submission_id="sub_999",
        func_report=mock_func_report,
        static_metrics=mock_static_metrics
    )
    
    assert report.submission_id == "sub_999"
    assert report.functionality_score == 100.0
    assert report.code_quality_score == 90.0  # 100 - (2 * 5)
    assert report.efficiency_score == 100.0   # No penalties
    assert report.final_weighted_grade == 9.8 # (60 + 18 + 20) / 10
    assert report.verdict == "ACCEPTED_EXCELLENT"