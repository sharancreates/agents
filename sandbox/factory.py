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
        logger.warning("E2B provider requested but E2B_API_KEY is missing. Falling back to safe fallback.")

    if provider_name == "docker":
        docker_provider = DockerSandboxProvider()
        if docker_provider.is_available():
            return docker_provider
        logger.warning("Docker provider requested but Docker daemon is unreachable. Falling back to safe fallback.")

    if provider_name == "fallback":
        return RestrictedFallbackProvider()

    # Auto resolution mode: try Docker -> E2B -> Fallback
    docker_provider = DockerSandboxProvider()
    if docker_provider.is_available():
        return docker_provider

    e2b_provider = E2BSandboxProvider()
    if e2b_provider.is_available():
        return e2b_provider

    logger.info("Using RestrictedFallbackProvider for sandbox execution.")
    return RestrictedFallbackProvider()
