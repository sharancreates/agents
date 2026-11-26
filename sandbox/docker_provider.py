import os
import sys
import time
import shutil
import tempfile
import subprocess
import logging
from typing import List, Optional
from sandbox.base import BaseSandboxProvider
from sandbox.models import SandboxConfig, SandboxExecutionRequest, SandboxResult

logger = logging.getLogger("DockerSandboxProvider")

class DockerSandboxProvider(BaseSandboxProvider):
    """Executes code inside an ephemeral Docker container with strict Linux namespaces and cgroups."""

    def __init__(self, default_image: Optional[str] = None):
        self.default_image = default_image or os.getenv("SANDBOX_DOCKER_IMAGE", "python:3.10-slim")
        self._docker_bin = shutil.which("docker") or "docker"

    def is_available(self) -> bool:
        """Verifies if docker CLI exists and the daemon responds."""
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(
                [self._docker_bin, "info", "--format", "{{.ServerVersion}}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2.0
            )
            return res.returncode == 0
        except Exception:
            return False

    def execute(self, request: SandboxExecutionRequest) -> SandboxResult:
        cfg = request.config or SandboxConfig()
        image = cfg.image or self.default_image

        # Prepare temporary directory for mounting
        with tempfile.TemporaryDirectory(prefix="autojudge_sandbox_") as temp_dir:
            target_filename = "main.py"
            if request.language in ("javascript", "js"):
                target_filename = "main.js"
            elif request.language in ("typescript", "ts"):
                target_filename = "main.ts"

            dest_path = os.path.join(temp_dir, target_filename)

            if request.code is not None:
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(request.code)
            elif request.script_path and os.path.exists(request.script_path):
                shutil.copyfile(request.script_path, dest_path)
            else:
                return SandboxResult(
                    status="FAILED",
                    exit_code=1,
                    stderr=f"Error: Target script not found: {request.script_path}"
                )

            # Determine runtime command inside container
            if request.language == "python":
                cmd = ["python3", "-u", f"/sandbox_env/{target_filename}"]
            elif request.language in ("javascript", "js"):
                cmd = ["node", f"/sandbox_env/{target_filename}"]
            elif request.language in ("typescript", "ts"):
                cmd = ["ts-node", f"/sandbox_env/{target_filename}"]
            else:
                cmd = ["python3", "-u", f"/sandbox_env/{target_filename}"]

            # Normalize temp_dir path for Docker volume mounting on Windows/Linux
            mount_path = os.path.abspath(temp_dir).replace("\\", "/")

            docker_cmd = [
                self._docker_bin, "run", "--rm", "-i",
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true",
                "--user", "1000:1000",
                "--memory", f"{cfg.memory_limit_mb}m",
                "--memory-swap", f"{cfg.memory_limit_mb}m",
                "--cpus", str(cfg.cpu_limit),
                "--pids-limit", str(cfg.pids_limit),
                "-v", f"{mount_path}:/sandbox_env:ro",
                "-w", "/sandbox_env"
            ]

            if not cfg.allow_network:
                docker_cmd.extend(["--network", "none"])

            docker_cmd.append(image)
            docker_cmd.extend(cmd)

            start_time = time.perf_counter()
            try:
                proc = subprocess.Popen(
                    docker_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout_data, stderr_data = proc.communicate(
                    input=request.stdin_data or None,
                    timeout=cfg.timeout_seconds
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                oom_killed = False
                timed_out = False
                status = "COMPLETED"

                # Exit code 137 in Docker indicates SIGKILL (often OOM or manual kill)
                if proc.returncode == 137:
                    status = "OOM_KILLED"
                    oom_killed = True
                    stderr_data = (stderr_data or "") + "\nPROCESS_KILLED: Out of Memory (OOM) limit exceeded."
                elif proc.returncode != 0:
                    status = "FAILED"

                return SandboxResult(
                    status=status,
                    exit_code=proc.returncode,
                    stdout=stdout_data or "",
                    stderr=stderr_data or "",
                    duration_ms=round(duration_ms, 2),
                    peak_memory_bytes=0, # In cgroups, limits enforced at kernel level
                    timed_out=timed_out,
                    oom_killed=oom_killed
                )

            except subprocess.TimeoutExpired:
                duration_ms = cfg.timeout_seconds * 1000.0
                try:
                    proc.kill()
                    proc.communicate()
                except Exception:
                    pass

                return SandboxResult(
                    status="TIMEOUT",
                    exit_code=124,
                    stdout="",
                    stderr=f"TIMEOUT_FAILURE: Execution exceeded deadline of {cfg.timeout_seconds}s.",
                    duration_ms=round(duration_ms, 2),
                    timed_out=True
                )
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxResult(
                    status="FAILED",
                    exit_code=1,
                    stdout="",
                    stderr=f"DOCKER_SANDBOX_ERROR: {str(e)}",
                    duration_ms=round(duration_ms, 2)
                )
