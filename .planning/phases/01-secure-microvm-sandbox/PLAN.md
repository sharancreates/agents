# Phase 1: Implementation Plan - Secure MicroVM Execution Sandbox

```
Mode: tracer-first
Status: planned
Target: 01-secure-microvm-sandbox
```

---

## Task Breakdown

### Task 1: [TRACER SLICE] Core Sandbox Models & Docker Provider
**Goal**: Build the foundational sandbox contract and a working Docker-based isolated execution provider.
- **Files to create/modify**:
  - `sandbox/models.py`: Schemas for `SandboxConfig`, `SandboxExecutionRequest`, `SandboxResult`.
  - `sandbox/base.py`: `BaseSandboxProvider` abstract class.
  - `sandbox/docker_provider.py`: `DockerSandboxProvider` executing code via Docker CLI / API with strict isolation flags (`--network none`, `--memory 256m`, `--pids-limit 64`, `--read-only`, tmpfs).
  - `sandbox/factory.py`: `get_sandbox_provider()` factory resolving the active provider.
- **Verification**: Run a tracer test executing a simple Python print command inside the isolated Docker sandbox, asserting `exit_code == 0` and stdout captured.

---

### Task 2: Cloud MicroVM Provider (E2B) & Safe Fallback Provider
**Goal**: Support serverless cloud microVM execution for production SaaS and mock fallback for non-containerized CI.
- **Files to create/modify**:
  - `sandbox/e2b_provider.py`: `E2BSandboxProvider` using the E2B Python SDK for cloud microVM execution.
  - `sandbox/fallback_provider.py`: `RestrictedFallbackProvider` with safe mocked/isolated subprocess execution for unit testing without Docker.
  - `sandbox/factory.py`: Support dynamic selection (`SANDBOX_PROVIDER=docker|e2b|fallback`).
- **Verification**: Run tests against `fallback_provider` and `e2b_provider` (mocked / live if key configured) verifying uniform interface adherence.

---

### Task 3: Refactor Dynamic Runner to Use Sandbox Provider
**Goal**: Discontinue host-level execution in `person_2/functionality/runner.py`.
- **Files to create/modify**:
  - `person_2/functionality/runner.py`:
    - Replace host `subprocess.Popen` in `DynamicExecutionRunner.execute_script()` with `get_sandbox_provider().execute(...)`.
    - Batch test suite execution to minimize container startup overhead.
    - Transform sandbox results into `TestCaseResult` and `FunctionalityReport`.
- **Verification**: Run existing tests `pytest person_2/tests/test_functionality.py` and confirm all test cases pass without regressions.

---

### Task 4: Scoring Engine & Worker Pipeline Integration
**Goal**: Surface sandbox telemetry (RAM, duration, timeout, OOM) in judge scoring and database status.
- **Files to create/modify**:
  - `person_2/functionality/scoring.py`:
    - Add scoring penalties and warning flags when code triggers OOM, timeouts, or security violations.
  - `orchestrator/celery_app.py`:
    - Capture new sandbox security metrics and pass them into `sub.functionality["raw_metrics"]` and flags.
- **Verification**: Run `python -m pytest person_2/tests/test_aggregator.py` and verify metrics propagation.

---

### Task 5: Adversarial Security & Boundary Test Suite
**Goal**: Verify that malicious code cannot compromise the host, escape the sandbox, or starve host resources.
- **Files to create/modify**:
  - `person_2/tests/test_sandbox_security.py`:
    - `test_normal_execution`: Standard script succeeds with correct output.
    - `test_infinite_loop_timeout`: CPU spin triggers `TIMEOUT_EXPIRED` cleanly within specified seconds.
    - `test_memory_bomb_oom`: Memory exhaustion triggers `OOM_KILLED` without crashing host services.
    - `test_fork_bomb_mitigation`: Recursive process spawn blocked by PID quota.
    - `test_network_egress_blocked`: Outbound socket / HTTP request rejected.
    - `test_filesystem_write_isolation`: Attempting to write to root or read host secrets fails.
- **Verification**: Run `python -m pytest person_2/tests/test_sandbox_security.py` and verify all security assertions pass.
