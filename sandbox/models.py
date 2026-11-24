from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class SandboxConfig(BaseModel):
    """Resource and security constraints for sandbox execution."""
    timeout_seconds: float = Field(default=2.0, description="Maximum execution time in seconds.")
    memory_limit_mb: int = Field(default=256, description="Maximum memory allocation in megabytes.")
    cpu_limit: float = Field(default=1.0, description="CPU core quota allocation.")
    pids_limit: int = Field(default=64, description="Maximum number of concurrent processes.")
    read_only: bool = Field(default=True, description="Enforce read-only root filesystem.")
    allow_network: bool = Field(default=False, description="Whether outbound network connectivity is permitted.")
    image: str = Field(default="ubuntu:22.04", description="Container image to use for execution.")

class SandboxExecutionRequest(BaseModel):
    """Payload representing an execution job inside the sandbox."""
    code: Optional[str] = Field(default=None, description="Direct source code to execute.")
    script_path: Optional[str] = Field(default=None, description="Path to script file if executing from disk.")
    language: str = Field(default="python", description="Target runtime language: python, javascript, typescript.")
    stdin_data: str = Field(default="", description="Data piped to standard input.")
    config: SandboxConfig = Field(default_factory=SandboxConfig, description="Execution limits.")

class SandboxResult(BaseModel):
    """Execution outcome, metrics, and security diagnostics."""
    status: str = Field(default="COMPLETED", description="COMPLETED, TIMEOUT, OOM_KILLED, SECURITY_VIOLATION, FAILED")
    exit_code: int = Field(default=0, description="Process return code.")
    stdout: str = Field(default="", description="Captured standard output.")
    stderr: str = Field(default="", description="Captured standard error.")
    duration_ms: float = Field(default=0.0, description="Total runtime duration in milliseconds.")
    peak_memory_bytes: int = Field(default=0, description="Peak memory consumed in bytes.")
    timed_out: bool = Field(default=False, description="Flag indicating execution deadline exceeded.")
    oom_killed: bool = Field(default=False, description="Flag indicating process killed due to memory limit.")
    security_violation: Optional[str] = Field(default=None, description="Details of blocked security violation.")
