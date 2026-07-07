import sys
import time
import subprocess
import os
import shutil
from typing import List
from person_2.functionality.models import TestCaseInput, FunctionalityConfig, TestCaseResult, FunctionalityReport

class DynamicExecutionRunner:
    """Safely executes multi-language third-party submission scripts and profiles exact execution metrics."""

    @classmethod
    def _get_peak_memory_linux(cls, pid: int) -> int:
        """Extracts peak resident set size memory (VmHWM) in bytes from Linux proc filesystem."""
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
        """Leverages ctypes kernel bindings to query the process peak working set memory size."""
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
    def _resolve_runtime_args(cls, script_path: str) -> List[str]:
        """Routes execution strategy based on file extension mapping."""
        _, ext = os.path.splitext(script_path.lower())
        
        if ext == ".py":
            return [sys.executable, script_path]
        elif ext == ".js":
            node_exe = shutil.which("node") or "node"
            return [node_exe, script_path]
        elif ext == ".ts":
            # Uses ts-node for dynamic execution if available, falls back to node
            ts_node_exe = shutil.which("ts-node") or "ts-node"
            return [ts_node_exe, script_path]
        else:
            raise ValueError(f"Unsupported environment extension: '{ext}'")

    @classmethod
    def execute_script(
        cls, script_path: str, test_cases: List[TestCaseInput], config: FunctionalityConfig
    ) -> FunctionalityReport:
        breakdown = []
        passed_count = 0
        global_peak_memory = 0

        # Strategy routing based on script language profile
        try:
            cmd_args = cls._resolve_runtime_args(script_path)
        except Exception as e:
            return FunctionalityReport(
                total_tests=len(test_cases),
                passed_tests=0,
                success_rate=0.0,
                peak_memory_bytes=0,
                test_breakdown=[],
                error_summary=f"ROUTING_ERROR: {str(e)}"
            )

        for tc in test_cases:
            start_time = time.perf_counter()
            err_msg = None
            observed = ""
            passed = False
            case_peak_memory = 0
            proc = None

            try:
                # Spawn process with language-specific routing args
                proc = subprocess.Popen(
                    cmd_args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                # Write standard inputs to the process pipe immediately
                if tc.input_data:
                    proc.stdin.write(tc.input_data)
                proc.stdin.close() 

                # Active monitoring loop to profile memory usage while execution progresses
                timeout_threshold = time.time() + config.timeout_seconds
                while proc.poll() is None:
                    if time.time() > timeout_threshold:
                        proc.kill()
                        raise subprocess.TimeoutExpired(proc.args, config.timeout_seconds)
                    
                    if os.name == "nt":
                        mem = cls._get_peak_memory_windows(int(proc._handle))
                    else:
                        mem = cls._get_peak_memory_linux(proc.pid)
                    
                    if mem > case_peak_memory:
                        case_peak_memory = mem
                    time.sleep(0.005)

                # Read outputs safely
                stdout, stderr = proc.communicate()
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                observed = stdout.strip() if stdout else ""
                
                if proc.returncode != 0:
                    err_msg = stderr.strip() if stderr else f"Process exited with non-zero code: {proc.returncode}"
                elif observed == tc.expected_output.strip():
                    passed = True
                    passed_count += 1

            except subprocess.TimeoutExpired as te:
                duration_ms = config.timeout_seconds * 1000.0
                err_msg = f"TIMEOUT_FAILURE: Execution exceeded maximum runtime limit of {config.timeout_seconds}s."
                if proc:
                    proc.kill()
                    stdout, stderr = proc.communicate()
                    observed = stdout.strip() if stdout else ""
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                err_msg = f"SYSTEM_CRASH: {str(e)}"
                if proc and proc.poll() is None:
                    proc.kill()

            if case_peak_memory > global_peak_memory:
                global_peak_memory = case_peak_memory

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
            peak_memory_bytes=global_peak_memory,
            test_breakdown=breakdown
        )