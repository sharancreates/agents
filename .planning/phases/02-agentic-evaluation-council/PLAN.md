# Phase 2: Implementation Plan - Agentic Evaluation Council

```
Mode: tracer-first
Status: planned
Target: 02-agentic-evaluation-council
```

---

## Task Breakdown

### Task 1: [TRACER SLICE] Council State & Autonomous Recon Agent
**Goal**: Build the typed state graph foundation and the repository discovery agent.
- **Files to create/modify**:
  - `agents/council/__init__.py`
  - `agents/council/state.py`: `CouncilState`, `AgentTraceEvent`, `EnvironmentBlueprint`, `DimensionEvaluation`.
  - `agents/council/recon_agent.py`: `ReconAgent` discovering stack, dependencies, README purpose, and entrypoints.
- **Verification**: Run tracer test inspecting a sample repository and confirming that `CouncilState.environment` is accurately populated with runtime, entrypoint, and discovered frameworks.

---

### Task 2: Dynamic QA & Adversarial Test Synthesizer
**Goal**: Implement autonomous test generation that creates and runs tests against submissions dynamically.
- **Files to create/modify**:
  - `agents/council/qa_agent.py`:
    - Synthesizes `TestCaseInput` blocks based on the challenge specification and detected entrypoint arguments/routes.
    - Runs generated test suite through `get_sandbox_provider()`.
    - Handles timeouts, errors, and output verification.
- **Verification**: Test that `QAAgent` generates valid test cases for a target script, runs them in the sandbox, and produces a `FunctionalityReport`.

---

### Task 3: Semantic Code Quality & Git Forensics Agents
**Goal**: Deep code inspection combining AST structural analysis with semantic review and git history forensics.
- **Files to create/modify**:
  - `agents/council/quality_agent.py`:
    - Audits architecture patterns, error handling, security posture, and complexity.
    - Cites specific file lines for all findings.
  - `agents/council/forensics_agent.py`:
    - Inspects git commit timelines, commit sizes, author consistency, and vector plagiarism metrics.
- **Verification**: Verify that both agents populate `CouncilState` with evidence-backed findings and numeric dimension grades.

---

### Task 4: Critic Adjudicator, Feedback Coach & Council Orchestrator
**Goal**: Build the deliberation consensus engine and participant feedback generator.
- **Files to create/modify**:
  - `agents/council/critic_agent.py`:
    - Reconciles findings between QA, Quality, and Forensics.
    - Strips unsupported penalties that lack line citations or sandbox logs.
    - Calculates final calibrated scores based on rubric weights.
  - `agents/council/feedback_agent.py`:
    - Produces constructive participant commentary (strengths, growth areas, actionable recommendations).
  - `agents/council/orchestrator.py`:
    - `CouncilOrchestrator` coordinating graph state transitions, error handling, and trace recording.
- **Verification**: Run end-to-end deliberation test confirming that Critic resolves conflicts and outputs a finalized `CouncilEvaluationDossier`.

---

### Task 5: Celery Worker Integration & Council Test Suite
**Goal**: Connect the Council into the backend task pipeline and verify full functionality.
- **Files to create/modify**:
  - `orchestrator/celery_app.py`:
    - Integrate `CouncilOrchestrator.evaluate()` into `process_submission_task`.
  - `person_2/tests/test_agent_council.py`:
    - Full automated test suite verifying state flow, dynamic test generation, sandbox execution, critic calibration, and feedback formatting.
- **Verification**: Run `pytest person_2/tests/test_agent_council.py -v` and assert all council stages complete successfully.
