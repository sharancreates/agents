import os
import time
import logging
from typing import Optional
from sandbox.base import BaseSandboxProvider
from sandbox.models import SandboxConfig, SandboxExecutionRequest, SandboxResult

logger = logging.getLogger("E2BSandboxProvider")

class E2BSandboxProvider(BaseSandboxProvider):
    """
    Cloud Serverless MicroVM sandbox provider powered by E2B (Firecracker microVMs).
    Enables zero-infrastructure hardware-level isolation for production multi-tenant deployments.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY")

    def is_available(self) -> bool:
        """Available if E2B_API_KEY is configured in the environment and e2b_code_interpreter is installed."""
        if not (self.api_key and len(self.api_key.strip()) > 0):
            return False
        try:
            import e2b_code_interpreter
            return True
        except ImportError:
            return False

    def execute(self, request: SandboxExecutionRequest) -> SandboxResult:
        if not self.is_available():
            return SandboxResult(
                status="FAILED",
                exit_code=1,
                stderr="E2B_SANDBOX_ERROR: E2B_API_KEY is missing or 'e2b_code_interpreter' SDK is not installed.",
                duration_ms=0.0
            )

        cfg = request.config or SandboxConfig()
        start_time = time.perf_counter()

        try:
            # Pluggable dynamic import of e2b_code_interpreter
            from e2b_code_interpreter import Sandbox

            # Initialize ephemeral cloud microVM with configured timeout
            with Sandbox(api_key=self.api_key, timeout=int(cfg.timeout_seconds) + 5) as sandbox:
                # If script file is specified, read code
                code_content = request.code or ""
                if not code_content and request.script_path and os.path.exists(request.script_path):
                    with open(request.script_path, "r", encoding="utf-8", errors="ignore") as f:
                        code_content = f.read()

                # Feed request test-case stdin into execution environment
                if request.stdin_data:
                    stdin_repr = repr(request.stdin_data)
                    if request.language == "python" or not request.language:
                        code_content = f"import sys, io\nsys.stdin = io.StringIO({stdin_repr})\n" + code_content

                execution = sandbox.run_code(code_content)
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                stdout_text = "\n".join(execution.logs.stdout) if execution.logs.stdout else ""
                stderr_text = "\n".join(execution.logs.stderr) if execution.logs.stderr else ""

                if execution.error:
                    stderr_text += f"\n{execution.error.name}: {execution.error.value}"

                return SandboxResult(
                    status="COMPLETED" if not execution.error else "FAILED",
                    exit_code=0 if not execution.error else 1,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    duration_ms=round(duration_ms, 2)
                )

        except ImportError:
            return SandboxResult(
                status="FAILED",
                exit_code=1,
                stderr="E2B_SANDBOX_ERROR: 'e2b_code_interpreter' package is not installed.",
                duration_ms=0.0
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SandboxResult(
                status="FAILED",
                exit_code=1,
                stderr=f"E2B_EXECUTION_EXCEPTION: {str(e)}",
                duration_ms=round(duration_ms, 2)
            )
