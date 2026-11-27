import os
import logging
from typing import Optional
from sandbox.base import BaseSandboxProvider
from sandbox.docker_provider import DockerSandboxProvider
from sandbox.e2b_provider import E2BSandboxProvider
from sandbox.fallback_provider import RestrictedFallbackProvider

logger = logging.getLogger("SandboxFactory")

def get_sandbox_provider(requested_provider: Optional[str] = None) -> BaseSandboxProvider:
    """
    Resolves the appropriate sandbox provider based on requested preference,
    environment configuration, and runtime backend availability.
    """
    provider_name = (requested_provider or os.getenv("SANDBOX_PROVIDER", "auto")).lower()

    if provider_name == "e2b":
        e2b_provider = E2BSandboxProvider()
        if e2b_provider.is_available():
            return e2b_provider
        logger.warning("E2B provider explicitly requested but unavailable.")
        if os.getenv("ALLOW_UNSAFE_FALLBACK", "false").lower() in ("true", "1"):
            return RestrictedFallbackProvider()
        raise RuntimeError("Requested sandbox provider 'e2b' is not available (E2B_API_KEY missing or SDK not installed).")

    if provider_name == "docker":
        docker_provider = DockerSandboxProvider()
        if docker_provider.is_available():
            return docker_provider
        logger.warning("Docker provider explicitly requested but Docker daemon is unreachable.")
        if os.getenv("ALLOW_UNSAFE_FALLBACK", "false").lower() in ("true", "1"):
            return RestrictedFallbackProvider()
        raise RuntimeError("Requested sandbox provider 'docker' is not available (Docker daemon unreachable).")

    if provider_name == "fallback":
        if os.getenv("ALLOW_UNSAFE_FALLBACK", "false").lower() in ("true", "1") or os.getenv("PYTEST_CURRENT_TEST"):
            return RestrictedFallbackProvider()
        raise RuntimeError("RestrictedFallbackProvider requires explicit ALLOW_UNSAFE_FALLBACK=true opt-in.")

    # Auto resolution mode: try Docker -> E2B -> Fallback (only with opt-in or test mode)
    docker_provider = DockerSandboxProvider()
    if docker_provider.is_available():
        return docker_provider

    e2b_provider = E2BSandboxProvider()
    if e2b_provider.is_available():
        return e2b_provider

    if os.getenv("ALLOW_UNSAFE_FALLBACK", "false").lower() in ("true", "1") or os.getenv("PYTEST_CURRENT_TEST"):
        logger.info("Using RestrictedFallbackProvider for sandbox execution (controlled test mode).")
        return RestrictedFallbackProvider()

    raise RuntimeError(
        "No secure sandbox provider is available (Docker daemon unreachable and E2B_API_KEY unset). "
        "Set ALLOW_UNSAFE_FALLBACK=true to permit host execution in development."
    )
