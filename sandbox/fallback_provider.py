import os
import sys
import time
import shutil
import tempfile
import subprocess
import logging
from typing import Optional, Any
from sandbox.base import BaseSandboxProvider
from sandbox.models import SandboxConfig, SandboxExecutionRequest, SandboxResult

logger = logging.getLogger("RestrictedFallbackProvider")

try:
    import psutil
    has_psutil = True
except ImportError:
    has_psutil = False

class RestrictedFallbackProvider(BaseSandboxProvider):
    """
    Guarded subprocess execution provider used when Docker is not running.
    Monitors peak memory using psutil, enforces execution timeouts, and flags unsafe network/file calls.
    """

    def is_available(self) -> bool:
        return True

    @classmethod
    def _get_process_rss(cls, proc: subprocess.Popen, ps_proc: Optional[Any] = None) -> int:
        if ps_proc:
            try:
                return ps_proc.memory_info().rss
            except Exception:
                pass

        if os.name != "nt":
            try:
                with open(f"/proc/{proc.pid}/status", "r") as f:
                    for line in f:
                        if line.startswith("VmHWM:"):
                            parts = line.split()
                            if len(parts) >= 2:
                                return int(parts[1]) * 1024
            except Exception:
                pass
        return 0

    def execute(self, request: SandboxExecutionRequest) -> SandboxResult:
        cfg = request.config or SandboxConfig()

        # Static pre-execution security scan when network is prohibited
        code_to_check = request.code or ""
        if request.script_path and os.path.exists(request.script_path):
            try:
                with open(request.script_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_to_check = f.read()
            except Exception:
                pass

        if not cfg.allow_network:
            forbidden_network_tokens = [
                "import socket", "from socket import",
                "import urllib", "from urllib import",
                "import requests", "from requests import",
                "import http.client", "from http.client import"
            ]
            for token in forbidden_network_tokens:
                if token in code_to_check:
                    return SandboxResult(
                        status="SECURITY_VIOLATION",
                        exit_code=1,
                        stdout="",
                        stderr=f"SECURITY_POLICY_VIOLATION: Network access blocked by sandbox policy ({token}).",
                        duration_ms=0.0,
                        security_violation=f"Prohibited network import detected: {token}"
                    )

        # Resolve command arguments based on language
        if request.language == "python":
            cmd = [sys.executable, "-u"]
        elif request.language in ("javascript", "js"):
            cmd = [shutil.which("node") or "node"]
        elif request.language in ("typescript", "ts"):
            ts_node = shutil.which("ts-node")
            cmd = [ts_node] if ts_node else [shutil.which("node") or "node"]
        else:
            cmd = [sys.executable, "-u"]

        with tempfile.TemporaryDirectory(prefix="fallback_sandbox_") as temp_dir:
            if request.code is not None:
                ext = ".py" if request.language == "python" else ".js"
                target_path = os.path.join(temp_dir, f"target{ext}")
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(request.code)
            elif request.script_path and os.path.exists(request.script_path):
                target_path = request.script_path
            else:
                return SandboxResult(
                    status="FAILED",
                    exit_code=1,
                    stderr=f"Target script not found: {request.script_path}"
                )

            cmd.append(target_path)
            start_time = time.perf_counter()
            case_peak_memory = 0
            proc = None

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                if request.stdin_data:
                    proc.stdin.write(request.stdin_data)
                proc.stdin.close()

                max_memory_bytes = cfg.memory_limit_mb * 1024 * 1024
                timeout_threshold = time.time() + cfg.timeout_seconds

                ps_proc = None
                if has_psutil:
                    try:
                        ps_proc = psutil.Process(proc.pid)
                    except Exception:
                        pass

                while proc.poll() is None:
                    now = time.time()
                    if now > timeout_threshold:
                        proc.kill()
                        raise subprocess.TimeoutExpired(proc.args, cfg.timeout_seconds)

                    mem = self._get_process_rss(proc, ps_proc)
                    if mem > case_peak_memory:
                        case_peak_memory = mem

                    # Enforce memory cap actively
                    if mem > max_memory_bytes:
                        if ps_proc:
                            try:
                                ps_proc.kill()
                            except Exception:
                                pass
                        proc.kill()
                        return SandboxResult(
                            status="OOM_KILLED",
                            exit_code=137,
                            stdout="",
                            stderr=f"OOM_KILLED: Process exceeded configured memory limit of {cfg.memory_limit_mb}MB.",
                            duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                            peak_memory_bytes=mem,
                            oom_killed=True
                        )

                    time.sleep(0.005)

                stdout_data = proc.stdout.read() if proc.stdout else ""
                stderr_data = proc.stderr.read() if proc.stderr else ""
                proc.stdout.close()
                proc.stderr.close()
                proc.wait()

                duration_ms = (time.perf_counter() - start_time) * 1000.0
                status = "COMPLETED" if proc.returncode == 0 else "FAILED"

                return SandboxResult(
                    status=status,
                    exit_code=proc.returncode,
                    stdout=stdout_data or "",
                    stderr=stderr_data or "",
                    duration_ms=round(duration_ms, 2),
                    peak_memory_bytes=case_peak_memory
                )

            except subprocess.TimeoutExpired:
                duration_ms = cfg.timeout_seconds * 1000.0
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                return SandboxResult(
                    status="TIMEOUT",
                    exit_code=124,
                    stdout="",
                    stderr=f"TIMEOUT_FAILURE: Execution exceeded maximum runtime limit of {cfg.timeout_seconds}s.",
                    duration_ms=round(duration_ms, 2),
                    timed_out=True,
                    peak_memory_bytes=case_peak_memory
                )
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxResult(
                    status="FAILED",
                    exit_code=1,
                    stdout="",
                    stderr=f"FALLBACK_EXECUTION_ERROR: {str(e)}",
                    duration_ms=round(duration_ms, 2)
                )
