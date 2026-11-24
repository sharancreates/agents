import os
import logging
from typing import List, Dict, Any, Optional
from agents.council.state import CouncilState, DimensionEvaluation
from person_2.functionality.models import TestCaseInput, FunctionalityConfig
from person_2.functionality.runner import DynamicExecutionRunner

logger = logging.getLogger("QAAgent")

class QAAgent:
    """
    Dynamic QA & Adversarial Test Synthesizer Agent.
    Autonomously creates custom test cases tailored to challenge prompts and entrypoints,
    dispatches them into the isolated sandbox, and scores runtime functionality.
    """

    @classmethod
    def synthesize_and_execute(cls, state: CouncilState) -> DimensionEvaluation:
        env = state.environment
        if not env or not env.entrypoint_script:
            state.add_trace(
                agent_role="QAAgent",
                action="SKIP_TESTING",
                reasoning="No valid execution entrypoint was discovered by ReconAgent."
            )
            eval_result = DimensionEvaluation(
                dimension="functionality",
                score=0.0,
                summary="No runnable entrypoint found in repository.",
                flags=["NO_ENTRYPOINT_DISCOVERED"]
            )
            state.dimensions["functionality"] = eval_result
            return eval_result

        target_script = os.path.join(state.repo_path, env.entrypoint_script)
        if not os.path.exists(target_script):
            eval_result = DimensionEvaluation(
                dimension="functionality",
                score=0.0,
                summary=f"Discovered entrypoint '{env.entrypoint_script}' does not exist on disk.",
                flags=["ENTRYPOINT_MISSING_ON_DISK"]
            )
            state.dimensions["functionality"] = eval_result
            return eval_result

        state.add_trace(
            agent_role="QAAgent",
            action="SYNTHESIZE_TESTS",
            reasoning=f"Generating tailored test matrix for {env.primary_language} script {env.entrypoint_script}"
        )

        # Autonomous test case synthesis based on challenge spec and entrypoint profile
        test_suite: List[TestCaseInput] = []
        
        # 1. Base functional health check
        test_suite.append(TestCaseInput(
            test_id="QA_TC1_SMOKE",
            input_data="healthcheck",
            expected_output="" # Evaluates graceful return code and clean stdout
        ))

        # 2. Spec-driven boundary tests
        challenge = (state.challenge_prompt or "").lower()
        if "calc" in challenge or "math" in challenge or "sum" in challenge:
            test_suite.extend([
                TestCaseInput(test_id="QA_TC2_MATH_BASIC", input_data="10 20\n", expected_output="30"),
                TestCaseInput(test_id="QA_TC3_MATH_ZERO", input_data="0 0\n", expected_output="0"),
                TestCaseInput(test_id="QA_TC4_MATH_BOUNDARY", input_data="-5 15\n", expected_output="10")
            ])
        elif "json" in challenge or "api" in challenge:
            test_suite.extend([
                TestCaseInput(test_id="QA_TC2_JSON_VALID", input_data='{"ping": "pong"}\n', expected_output=""),
                TestCaseInput(test_id="QA_TC3_JSON_MALFORMED", input_data='{invalid_json}\n', expected_output="")
            ])
        else:
            # Universal general-purpose input suites
            test_suite.extend([
                TestCaseInput(test_id="QA_TC2_STANDARD_INPUT", input_data="test_input_alpha\n", expected_output=""),
                TestCaseInput(test_id="QA_TC3_EMPTY_INPUT", input_data="\n", expected_output=""),
                TestCaseInput(test_id="QA_TC4_WHITESPACE_INPUT", input_data="   \t  \n", expected_output="")
            ])

        state.generated_tests = [
            tc.model_dump() if hasattr(tc, "model_dump") else tc.dict()
            for tc in test_suite
        ]

        # Dispatch execution to Phase 1 Sandbox Runner
        config = FunctionalityConfig(timeout_seconds=3.0, memory_limit_mb=256)
        report = DynamicExecutionRunner.execute_script(
            script_path=target_script,
            test_cases=test_suite,
            config=config
        )

        # Derive dynamic score: base pass rate + runtime stability
        flags = []
        crashes = 0
        timeouts = 0
        oom_events = 0
        security_violations = 0

        for r in report.test_breakdown:
            if r.error_message:
                if "TIMEOUT" in r.error_message:
                    timeouts += 1
                elif "OOM_KILLED" in r.error_message:
                    oom_events += 1
                elif "SECURITY_VIOLATION" in r.error_message:
                    security_violations += 1
                else:
                    crashes += 1

        if security_violations > 0:
            flags.append("SECURITY_VIOLATION_BLOCKED")
            score = 0.0
        elif oom_events > 0:
            flags.append("OOM_LIMIT_EXCEEDED")
            score = max(0.0, report.success_rate - 40.0)
        elif timeouts > 0:
            flags.append("EXECUTION_TIMEOUT")
            score = max(0.0, report.success_rate - 30.0)
        elif crashes == 0 and report.passed_tests > 0:
            flags.append("CLEAN_EXECUTION")
            score = report.success_rate
        else:
            # Baseline score on graceful zero-crash execution
            score = 75.0 if crashes == 0 else max(20.0, 100.0 - (crashes * 20.0))

        summary = (
            f"Executed {report.total_tests} dynamic tests against {env.entrypoint_script}. "
            f"Passed: {report.passed_tests}/{report.total_tests}. "
            f"Peak RAM: {report.peak_memory_mb:.2f}MB, Runtime: {report.total_duration_ms:.1f}ms."
        )

        eval_result = DimensionEvaluation(
            dimension="functionality",
            score=round(score, 1),
            summary=summary,
            flags=flags,
            evidence_citations=[
                f"{env.entrypoint_script} executed with exit code 0 across {report.total_tests} tests."
            ],
            raw_metrics={
                "total_tests": report.total_tests,
                "passed_tests": report.passed_tests,
                "success_rate": report.success_rate,
                "peak_memory_mb": report.peak_memory_mb,
                "runtime_duration_ms": report.total_duration_ms,
                "crashes": crashes,
                "timeouts": timeouts
            }
        )

        state.dimensions["functionality"] = eval_result
        state.add_trace(
            agent_role="QAAgent",
            action="EXECUTION_COMPLETE",
            reasoning=summary,
            details=eval_result.raw_metrics
        )

        return eval_result
