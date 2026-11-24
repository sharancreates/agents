import abc
from typing import List, Optional
from sandbox.models import SandboxConfig, SandboxExecutionRequest, SandboxResult

class BaseSandboxProvider(abc.ABC):
    """Abstract interface defining the execution contract for any sandbox provider."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Returns True if this provider backend is operational and reachable."""
        pass

    @abc.abstractmethod
    def execute(self, request: SandboxExecutionRequest) -> SandboxResult:
        """Executes the given request in the isolated sandbox environment."""
        pass

    def execute_script(
        self,
        script_path: str,
        stdin_data: str = "",
        config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """Convenience helper to execute a file script with language detection."""
        cfg = config or SandboxConfig()
        lang = "python"
        lower_path = script_path.lower()
        if lower_path.endswith(".js"):
            lang = "javascript"
        elif lower_path.endswith(".ts"):
            lang = "typescript"

        req = SandboxExecutionRequest(
            script_path=script_path,
            language=lang,
            stdin_data=stdin_data,
            config=cfg
        )
        return self.execute(req)
