import sys
import time
import subprocess
from typing import List
from person_2.functionality.models import TestCaseInput, FunctionalityConfig, TestCaseResult, FunctionalityReport

class DynamicExecutionRunner:
    """Safely executes third-party submission scripts inside isolated process contexts."""

    @classmethod
    def execute_python_script(
        cls, script_path: str, test_cases: List[TestCaseInput], config: FunctionalityConfig
    ) -> FunctionalityReport:
        breakdown = []
        passed_count = 0
        peak_mem = 0  # To be connected with advanced OS tracking hooks in upcoming milestones

        for tc in test_cases:
            start_time = time.perf_counter()
            err_msg = None
            observed = ""
            passed = False

            try:
                # Spawn an isolated subprocess running the targeted user code
                proc = subprocess.run(
                    [sys.executable, script_path],
                    input=tc.input_data,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout_seconds
                )
                
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                observed = proc.stdout.strip() if proc.stdout else ""
                
                if proc.returncode != 0:
                    err_msg = proc.stderr.strip() if proc.stderr else f"Process exited with non-zero code: {proc.returncode}"
                elif observed == tc.expected_output.strip():
                    passed = True
                    passed_count += 1

            except subprocess.TimeoutExpired as te:
                duration_ms = config.timeout_seconds * 1000.0
                err_msg = f"TIMEOUT_FAILURE: Execution exceeded maximum runtime limit of {config.timeout_seconds}s."
                observed = te.stdout.decode('utf-8', errors='ignore').strip() if te.stdout else ""
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                err_msg = f"SYSTEM_CRASH: {str(e)}"

            breakdown.append(TestCaseResult(
                test_id=tc.test_id,
                passed=passed,
                runtime_ms=round(duration_ms, 2),
                observed_output=observed,
                error_message=err_msg
            ))

        total = len(test_cases)
        rate = (passed_count / total * 100.0) if total > 0 else 0.0

        return FunctionalityReport(
            total_tests=total,
            passed_tests=passed_count,
            success_rate=round(rate, 2),
            peak_memory_bytes=peak_mem,
            test_breakdown=breakdown
        )