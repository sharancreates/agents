# Phase 1: Context & Scope

## 1. Phase Objective
Replace the insecure, host-level `subprocess` runner in [`person_2/functionality/runner.py`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/person_2/functionality/runner.py) with an isolated, resource-governed sandbox execution engine supporting both local Docker containers and cloud microVMs (E2B).

---

## 2. Scope Boundaries

### In Scope:
- **Sandbox Core Engine (`sandbox/`)**:
  - `sandbox/models.py`: Pydantic data schemas for sandbox execution requests, constraints, and results.
  - `sandbox/base.py`: Abstract Base Class defining standard execution contract.
  - `sandbox/docker_provider.py`: Docker-based isolated container runner with strict cgroups, tmpfs, read-only root, no network, and pids limit.
  - `sandbox/e2b_provider.py`: Cloud microVM provider integration via E2B SDK.
  - `sandbox/fallback_provider.py`: Mock/restricted runner for CI environments without Docker daemon.
  - `sandbox/factory.py`: Automatic provider selection based on environment configuration (`SANDBOX_PROVIDER=docker|e2b|fallback`).
- **Functionality Runner Refactoring**:
  - Update `person_2/functionality/runner.py` to route execution through `get_sandbox_provider()`.
  - Preserve backward compatibility with existing `TestCaseInput`, `TestCaseResult`, and `FunctionalityReport` schemas.
- **Worker & Scoring Alignment**:
  - Update `orchestrator/celery_app.py` and `person_2/functionality/scoring.py` to process sandbox security violation flags (e.g., `TIMEOUT`, `OOM_KILLED`, `SECURITY_VIOLATION_NETWORK_ATTEMPT`).
- **Security & Adversarial Testing**:
  - Create `person_2/tests/test_sandbox_security.py` verifying that dangerous operations fail safely without affecting the host.

### Out of Scope:
- LangGraph multi-agent judge council orchestration (deferred to Phase 2).
- Dynamic AI test generation from challenge prompts (deferred to Phase 2).
- Multi-tenancy and API key billing (deferred to Phases 3 and 4).

---

## 3. Technical Constraints & Decisions
1. **Zero Host Execution in Production**: Under no circumstances should untrusted submission code run on the host OS when `ENVIRONMENT != "test"`.
2. **Cross-Platform Host Support**: Development hosts may be Windows or Linux; the sandbox engine must use standard Docker commands or SDK that work seamlessly on Windows (Docker Desktop / WSL2) and Linux.
3. **Graceful Fallback**: If Docker is not running in a test/local environment, the fallback provider must log clear warnings and restrict basic calls without crashing the entire service.
