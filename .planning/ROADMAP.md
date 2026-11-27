# Roadmap: AutoJudge Agentic SaaS

## Phase Overview

```
Phase 1: Secure MicroVM Execution Sandbox [COMPLETED]
    │ (Eliminates critical host RCE risk, enables multi-language isolation)
    ▼
Phase 2: Agentic Evaluation Council [COMPLETED]
    │ (Converts deterministic scripts to autonomous ReAct/Critic agents)
    ▼
Phase 3: Multi-Tenancy, B2B Developer API & Webhooks [COMPLETED]
    │ (Organizations, API keys, webhook notifications, partner integration)
    ▼
Phase 4: Monetization Engine & Metered Billing (Razorpay) [COMPLETED]
    │ (Razorpay order checkout, HMAC-SHA256 signature verification, prepaid credit packages, HTTP 402 quota gating)
    ▼
Phase 4.5: Codebase & Rubric RAG Engine [COMPLETED]
    │ (AST code chunking, pgvector semantic search, sponsor bounty compliance, Judge Copilot API)
    ▼
Phase 5: Enterprise Portal & Real-Time Observability [COMPLETED]
    │ (Agent thought traces, live evaluation monitors, rubric customizer, developer console)
```

---

## Phase Details

### Phase 1: Secure MicroVM Execution Sandbox [COMPLETED]
- **Goal**: Replace host-level `subprocess` execution in `person_2/functionality/runner.py` with an isolated micro-sandbox.
- **Key Deliverables**:
  - [x] Sandbox abstraction layer (`sandbox/base.py`, `sandbox/models.py`).
  - [x] Pluggable Docker (`sandbox/docker_provider.py`), E2B Cloud MicroVM (`sandbox/e2b_provider.py`), and Guarded Fallback (`sandbox/fallback_provider.py`).
  - [x] Resource isolation (RAM capping, execution deadlines, blocked network egress, PID limit).
  - [x] Integration into `DynamicExecutionRunner` and `EvaluationScoringEngine`.
  - [x] Adversarial security test matrix (`person_2/tests/test_sandbox_security.py`) verifying infinite loop, memory bomb, and network attack handling.
- **Success Criteria**: 29/29 tests passing with 0 regressions. Untrusted malicious code fails safely without impacting the host system.

### Phase 2: Agentic Evaluation Council [COMPLETED]
- **Goal**: Replace linear Celery task execution with an autonomous multi-agent evaluation framework.
- **Key Deliverables**:
  - [x] Multi-agent state graph (`CouncilState`) tracking execution traces, blueprints, dimensions, and consensus verdicts.
  - [x] Discovery & Build Agent (`ReconAgent`) discovering stack, entrypoint, and package manifests.
  - [x] Dynamic QA Agent (`QAAgent`) synthesizing challenge-aligned test cases and executing them inside the sandbox.
  - [x] Semantic Quality Agent (`QualityAgent`) auditing cyclomatic complexity with line citations.
  - [x] Forensics Agent (`ForensicsAgent`) inspecting commit history and plagiarism indicators.
  - [x] Adversarial Critic Agent (`CriticAgent`) enforcing evidence-backed deductions and calibrating weighted grades.
  - [x] Participant Feedback Coach (`FeedbackCoach`) creating constructive growth and strength dossiers.
  - [x] Celery worker pipeline integration in `orchestrator/celery_app.py`.
  - [x] Automated test suite in `person_2/tests/test_agent_council.py` with 100% pass rate.
- **Success Criteria**: 36/36 tests passing with 0 regressions. System autonomously discovers entrypoints, tests code, debates evidence, and delivers calibrated verdicts.

### Phase 3: Multi-Tenancy, B2B Developer API & Webhooks [COMPLETED]
- **Goal**: Allow third-party platforms to integrate AutoJudge programmatically.
- **Key Deliverables**:
  - [x] Relational schema for `organizations`, `workspaces`, `api_keys`, and `webhook_endpoints`.
  - [x] Scoped API key generation (`ak_live_...`) with constant-time SHA-256 hash comparison.
  - [x] Tiered sliding-window rate limiting (Free: 10, Pro: 60, Enterprise: 300 req/min).
  - [x] Headless B2B REST endpoints (`POST /v1/evaluations`, `GET /v1/evaluations/{id}`, `GET /v1/evaluations/{id}/traces`, API key management).
  - [x] HMAC-SHA256 signed webhook dispatch engine with timestamp anti-replay verification.
  - [x] Automated test suite in `person_2/tests/test_b2b_api.py` with 100% pass rate.
- **Success Criteria**: 41/41 tests passing with 0 regressions. External platforms can authenticate, submit evaluations, receive webhooks, and stay segregated across tenants.

### Phase 4: Monetization Engine & Metered Billing (Razorpay) [COMPLETED]
- **Goal**: Enable self-serve and commercial B2B revenue capture via Razorpay payments and prepaid credits.
- **Key Deliverables**:
  - [x] Relational schema for `organization_credits`, `payment_orders`, and immutable `usage_events`.
  - [x] High-precision integer paise financial arithmetic (₹499 = 49900 paise, zero floating-point error).
  - [x] Razorpay Order client with offline simulation mode for CI and test environments.
  - [x] Cryptographic HMAC-SHA256 signature verification with double-spend and replay attack prevention.
  - [x] Headless REST billing endpoints (`GET /v1/billing/balance`, `POST /v1/billing/orders`, `POST /v1/billing/verify-payment`, `POST /v1/billing/razorpay-webhook`, `GET /v1/billing/usage`).
  - [x] Quota gating: HTTP 402 Payment Required when credits are depleted.
  - [x] Automated credit deduction hook upon Celery evaluation task completion.
  - [x] Automated test suite in `person_2/tests/test_razorpay_billing.py` (8/8 tests passed).
- **Success Criteria**: 49/49 tests passing across all test suites with 0 regressions. Verified payment capture, cryptographic signature validation, replay attack rejection, and HTTP 402 quota gating.

### Phase 4.5: Codebase & Rubric RAG Engine [COMPLETED]
- **Goal**: Implement AST-aware codebase semantic indexing, challenge rulebook/sponsor bounty compliance RAG, and an interactive "Chat with Submission / Ask AutoJudge" conversational endpoint using `pgvector` and `sentence-transformers`.
- **Key Deliverables**:
  - [x] Vector storage models: `CodeEmbedding` (functions, classes, route decorators with exact line ranges) and `RubricRequirement`.
  - [x] AST-aware code chunker & embedder producing 384-dimensional dense vectors with deterministic offline fallback.
  - [x] Council semantic retrieval tool (`search_codebase`) enabling agents to query multi-file codebases without context window exhaustion.
  - [x] Sponsor track and hackathon rule compliance auditor (`SponsorComplianceAuditor`) verifying specific SDKs and cloud targets with line-numbered citations.
  - [x] Conversational REST endpoint `POST /v1/evaluations/{id}/chat` allowing judges and organizers to query submissions with line-numbered evidence citations.
  - [x] Automated test suite in `person_2/tests/test_rag_engine.py` (7/7 tests passed).
- **Success Criteria**: 56/56 tests passing across all test suites with 0 regressions. Sub-second semantic code retrieval, 100% accurate sponsor bounty verification, and interactive Q&A citing line-numbered code evidence.

### Phase 5: Enterprise Portal & Real-Time Observability [COMPLETED]
- **Goal**: Provide hackathon organizers and platform admins with a complete control center.
- **Key Deliverables**:
  - [x] Real-time Server-Sent Events (SSE) streaming endpoint `GET /v1/evaluations/{id}/stream`.
  - [x] React Agent Deliberation Console (`AgentTraceStream.jsx`) showing stage progression and reasoning events.
  - [x] Interactive Rubric Customizer with 100% weight sum validation, custom prompts, and live previews.
  - [x] Developer & Billing Console (`/developer` - `DeveloperConsole.jsx`) for API key management, webhooks, and Razorpay credit top-ups.
  - [x] Embedded Judge Copilot Chat widget (`JudgeCopilot.jsx`) backed by the AST Codebase RAG engine.
  - [x] Automated test suite in `person_2/tests/test_portal_observability.py` (4/4 tests passed).
  - [x] Production Vite compilation verified (557ms build time).
- **Success Criteria**: 60/60 tests passing across all test suites with 0 regressions. Complete portal control center for organizers, judges, and developers.
