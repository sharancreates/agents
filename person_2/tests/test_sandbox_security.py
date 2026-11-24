import os
import pytest
from sandbox.factory import get_sandbox_provider
from sandbox.models import SandboxConfig, SandboxExecutionRequest
from person_2.functionality.models import TestCaseInput, FunctionalityConfig
from person_2.functionality.runner import DynamicExecutionRunner
from person_2.functionality.scoring import EvaluationScoringEngine

def test_sandbox_normal_execution(tmpdir):
    """Verifies that benign code executes accurately within the sandbox."""
    script = tmpdir.join("normal.py")
    script.write("print('SANDBOX_ACTIVE_42')\n")

    provider = get_sandbox_provider()
    result = provider.execute(SandboxExecutionRequest(
        script_path=str(script),
        language="python",
        config=SandboxConfig(timeout_seconds=2.0)
    ))

    assert result.status == "COMPLETED"
    assert result.exit_code == 0
    assert "SANDBOX_ACTIVE_42" in result.stdout
    assert not result.timed_out
    assert not result.oom_killed

def test_sandbox_infinite_loop_timeout(tmpdir):
    """Verifies that infinite loops are forcefully terminated by timeout constraints."""
    script = tmpdir.join("infinite.py")
    script.write("import time\nwhile True:\n    time.sleep(0.05)\n")

    provider = get_sandbox_provider()
    result = provider.execute(SandboxExecutionRequest(
        script_path=str(script),
        language="python",
        config=SandboxConfig(timeout_seconds=0.4)
    ))

    assert result.status == "TIMEOUT"
    assert result.timed_out is True
    assert "TIMEOUT_FAILURE" in result.stderr

def test_sandbox_network_isolation(tmpdir):
    """Verifies that unauthorized outbound network calls are rejected by the security policy."""
    script = tmpdir.join("network_attack.py")
    script.write("import socket\ns = socket.socket()\ns.connect(('8.8.8.8', 53))\n")

    provider = get_sandbox_provider()
    result = provider.execute(SandboxExecutionRequest(
        script_path=str(script),
        language="python",
        config=SandboxConfig(allow_network=False)
    ))

    # Should be flagged as security violation
    assert result.status == "SECURITY_VIOLATION"
    assert result.security_violation is not None
    assert "network" in result.security_violation.lower()

def test_sandbox_memory_governance(tmpdir):
    """Verifies that excessive memory allocation is detected and capped."""
    script = tmpdir.join("mem_hog.py")
    # Progressively allocates chunks so the active memory monitor catches and terminates it
    script.write("import time\ndata = []\nfor _ in range(80):\n    data.append(b'x' * (1024 * 1024))\n    time.sleep(0.01)\nprint('DONE')\n")

    provider = get_sandbox_provider()
    result = provider.execute(SandboxExecutionRequest(
        script_path=str(script),
        language="python",
        config=SandboxConfig(memory_limit_mb=25, timeout_seconds=3.0)
    ))

    assert result.status in ("OOM_KILLED", "FAILED") or result.oom_killed

def test_security_violation_triggers_disqualification(tmpdir):
    """Verifies that security violations produce a DISQUALIFIED verdict in the scoring engine."""
    script = tmpdir.join("malicious.py")
    script.write("import socket\nprint('ATTACK')\n")

    test_cases = [TestCaseInput(test_id="MAL1", input_data="", expected_output="ATTACK")]
    config = FunctionalityConfig(timeout_seconds=1.0)

    report = DynamicExecutionRunner.execute_script(str(script), test_cases, config)

    assert report.passed_tests == 0
    assert any("SECURITY_VIOLATION" in (tc.error_message or "") for tc in report.test_breakdown)

    grade = EvaluationScoringEngine.calculate_composite_grade(
        submission_id="sub_threat_test",
        func_report=report
    )

    assert grade.verdict == "DISQUALIFIED_SECURITY_POLICY"
    assert "SECURITY_VIOLATION_BLOCKED" in grade.flags
    assert grade.functionality_score == 0.0

def test_factory_fallback_resilience():
    """Verifies that the factory provides a working fallback when container daemon is offline."""
    provider = get_sandbox_provider("auto")
    assert provider is not None
    assert provider.is_available() is True
