# Phase 2: Context & Scope

## 1. Phase Objective
Construct the **Agentic Evaluation Council**—a multi-agent state graph that autonomously explores codebases, synthesizes dynamic functional test cases, executes them inside the Phase 1 sandbox, audits semantic code quality and git forensics, and runs an adversarial Critic deliberation loop to produce calibrated scores and participant feedback.

---

## 2. Scope Boundaries

### In Scope:
- **Council Architecture (`agents/council/`)**:
  - `state.py`: Typed Pydantic state model `CouncilState` tracking all intermediate agent outputs, traces, and final verdicts.
  - `recon_agent.py`: Autonomous discovery of repository structure, language, framework, and entrypoints.
  - `qa_agent.py`: Dynamic test synthesis matching challenge prompt specifications and execution in Phase 1 sandbox.
  - `quality_agent.py`: Semantic code review and architectural evaluation.
  - `forensics_agent.py`: Git commit cadence analysis and plagiarism detection.
  - `critic_agent.py`: Evidence-backed deliberation, score calibration, and conflict resolution.
  - `feedback_agent.py`: Constructive participant coaching generator.
  - `orchestrator.py`: `CouncilOrchestrator` coordinating graph transitions and error recovery.
- **Celery Worker Integration**:
  - Update `orchestrator/celery_app.py` to route evaluations through `CouncilOrchestrator`.
- **Verification & Test Suite**:
  - `person_2/tests/test_agent_council.py`: Full end-to-end multi-agent evaluation test suite.

### Out of Scope:
- B2B API Key database migration and rate limiting (deferred to Phase 3).
- Stripe / Lago billing integration (deferred to Phase 4).
- Frontend live WebSocket / SSE stream UI (deferred to Phase 5).

---

## 3. Interfaces & Contracts

### Input:
```python
class EvaluationTaskRequest(BaseModel):
    submission_id: str
    repo_path: str
    challenge_spec: Optional[ChallengeSpecification] = None
    rubric_weights: Optional[Dict[str, float]] = None
```

### Output:
```python
class CouncilEvaluationDossier(BaseModel):
    submission_id: str
    overall_score: float
    verdict: str
    dimensions: Dict[str, DimensionScore]
    participant_feedback: ParticipantFeedbackPackage
    agent_traces: List[AgentTraceEvent]
```
