# Technical Concerns, Vulnerabilities & Tech Debt

## 1. Critical Security Vulnerability: Untrusted Code Execution
- **Location**: `person_2/functionality/runner.py`
- **Severity**: **CRITICAL**
- **Issue**: `DynamicExecutionRunner.execute_script()` executes submitted Python/JS scripts directly on the host operating system using `subprocess.Popen([sys.executable, script_path])`.
- **Risk**: Any participant submission containing malicious code (e.g. `os.system("rm -rf /")`, malware, crypto miners, host credential exfiltration) will execute with the full privileges of the host server process.
- **Remediation**: Must isolate runtime execution inside dedicated ephemeral MicroVMs (e.g., Firecracker, E2B, Modal) or hard-sandboxed containers (Docker with gVisor `runsc`, restricted cgroups, read-only root, no network egress).

## 2. Multi-Tenancy & Authorization Gaps
- **Location**: `api/main.py`, `api/models.py`, `frontend/src/pages/Login.jsx`
- **Severity**: **HIGH**
- **Issue**:
  - The database currently has a flat `submissions` table without foreign keys for `organization_id`, `tenant_id`, or `user_id`.
  - API endpoints have no authentication or authorization middleware; anyone who can reach the API can submit code, trigger evaluations, or modify rubric weights.
  - The frontend login page simulates authentication using a timer and sets a username in `localStorage` without JWT or backend verification.
- **Remediation**: Implement an authentication layer (JWT / OAuth2), tenant/organization scoping, and hashed API keys with rate-limiting.

## 3. Deterministic Pipeline vs. Agentic Autonomy
- **Location**: `orchestrator/celery_app.py`, `api/synthesis_service.py`, `api/feedback_service.py`
- **Severity**: **MEDIUM-HIGH**
- **Issue**:
  - Despite being branded as "Multi-Agent", the evaluation is a rigid, sequential linear pipeline.
  - Test cases are static and hardcoded rather than dynamically synthesized to match the submission's purpose.
  - Scoring and feedback rely on fixed numerical threshold checks (`if score > 85: ...`) instead of intelligent multi-agent deliberation, self-correction, or critic reflection.
- **Remediation**: Migrate to a true multi-agent framework (e.g., LangGraph / Temporal) where agents autonomously discover entrypoints, synthesize test cases, execute in microVMs, and deliberate on scoring anomalies.

## 4. Operational & Scalability Bottlenecks
- **Location**: `orchestrator/celery_app.py`
- **Severity**: **MEDIUM**
- **Issue**:
  - A single Celery worker task (`process_submission_task`) runs all 4 evaluation stages sequentially inside one function. If stage 3 crashes or times out, stage 4 and synthesis may be interrupted unless handled carefully.
  - Heavy ML dependencies (`sentence-transformers`, `torch`) consume significant RAM inside worker processes.
- **Remediation**: Decompose into discrete Celery chords/workflows or independent microservice jobs so stages can scale and retry independently.
