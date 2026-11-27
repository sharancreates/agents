import os
import sys
import time
from typing import List, Optional
from person_2.functionality.models import TestCaseInput, FunctionalityConfig, TestCaseResult, FunctionalityReport
from sandbox.factory import get_sandbox_provider
from sandbox.models import SandboxConfig, SandboxExecutionRequest

class DynamicExecutionRunner:
    """Safely executes multi-language third-party submission scripts via isolated sandboxes."""

    @classmethod
    def _get_peak_memory_linux(cls, pid: int) -> int:
        """Helper for Linux proc memory inspection."""
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmHWM:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return int(parts[1]) * 1024
        except Exception:
            pass
        return 0

    @classmethod
    def _get_peak_memory_windows(cls, process_handle) -> int:
        """Helper for Windows kernel psapi memory inspection."""
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPoolUsage", ctypes.c_size_t),
                    ("QuotaPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                ]

            GetProcessMemoryCounters = ctypes.windll.psapi.GetProcessMemoryCounters
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            if GetProcessMemoryCounters(process_handle, ctypes.byref(counters), counters.cb):
                return counters.PeakWorkingSetSize
        except Exception:
            pass
        return 0

    @classmethod
    def execute_script(
        cls, script_path: str, test_cases: List[TestCaseInput], config: FunctionalityConfig
    ) -> FunctionalityReport:
        breakdown = []
        passed_count = 0
        global_peak_memory = 0

        if not os.path.exists(script_path):
            return FunctionalityReport(
                total_tests=len(test_cases),
                passed_tests=0,
                success_rate=0.0,
                peak_memory_bytes=0,
                test_breakdown=[],
                error_summary=f"TARGET_FILE_NOT_FOUND: '{script_path}' does not exist."
            )

        # Resolve language based on extension
        _, ext = os.path.splitext(script_path.lower())
        lang = "python"
        if ext in (".js", ".mjs"):
            lang = "javascript"
        elif ext in (".ts", ".tsx"):
            lang = "typescript"

        provider = get_sandbox_provider()
        memory_mb = getattr(config, "memory_limit_mb", 256) or 256

        sandbox_cfg = SandboxConfig(
            timeout_seconds=config.timeout_seconds,
            memory_limit_mb=memory_mb,
            allow_network=False
        )

        for tc in test_cases:
            req = SandboxExecutionRequest(
                script_path=script_path,
                language=lang,
                stdin_data=tc.input_data or "",
                config=sandbox_cfg
            )

            res = provider.execute(req)

            err_msg = None
            passed = False
            observed = res.stdout.strip() if res.stdout else ""

            if res.status == "TIMEOUT" or res.timed_out:
                err_msg = f"TIMEOUT_FAILURE: Execution exceeded maximum runtime limit of {config.timeout_seconds}s."
            elif res.status == "OOM_KILLED" or res.oom_killed:
                err_msg = f"OOM_KILLED: Process exceeded configured memory limit of {memory_mb}MB."
            elif res.status == "SECURITY_VIOLATION":
                err_msg = f"SECURITY_VIOLATION: {res.security_violation or res.stderr}"
            elif res.exit_code != 0:
                err_msg = res.stderr.strip() if res.stderr else f"Process exited with non-zero code: {res.exit_code}"
            elif observed == tc.expected_output.strip():
                passed = True
                passed_count += 1

            if res.peak_memory_bytes > global_peak_memory:
                global_peak_memory = res.peak_memory_bytes

            breakdown.append(TestCaseResult(
                test_id=tc.test_id,
                passed=passed,
                runtime_ms=round(res.duration_ms, 2),
                observed_output=observed,
                error_message=err_msg
            ))

        total = len(test_cases)
        rate = (passed_count / total * 100.0) if total > 0 else 0.0

        return FunctionalityReport(
            total_tests=total,
            passed_tests=passed_count,
            success_rate=round(rate, 2),
            peak_memory_bytes=global_peak_memory,
            test_breakdown=breakdown
        )
