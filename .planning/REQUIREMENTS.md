# Requirements: AutoJudge Agentic SaaS

## 1. Functional Requirements

### 1.1 Secure Remote Sandboxing (CRITICAL)
- **REQ-SEC-01**: Must execute untrusted code in an isolated environment (MicroVM via E2B/Modal or container with gVisor).
- **REQ-SEC-02**: Must enforce strict hardware quotas (CPU, RAM cap, disk write limit, process count) and execution deadlines.
- **REQ-SEC-03**: Must block arbitrary network egress from the sandbox while permitting required package installations via controlled proxies.

### 1.2 Agentic Evaluation Council
- **REQ-AGT-01 (Build Agent)**: Autonomously inspects codebase, identifies runtime dependencies, configures environment, and builds project.
- **REQ-AGT-02 (Adversarial QA Agent)**: Synthesizes dynamic functional tests and boundary cases tailored to the challenge prompt and tests live endpoints.
- **REQ-AGT-03 (Semantic Code Quality Agent)**: Evaluates architecture, maintainability, modularity, and security antipatterns beyond basic linter rules.
- **REQ-AGT-04 (Git Forensics Agent)**: Analyzes commit histories, commit intervals, author authenticity, and semantic similarity to detect plagiarism and boilerplate cloning.
- **REQ-AGT-05 (Critic & Consensus Agent)**: Deliberates on scoring discrepancies, validates evidence with code citations, and generates verified scorecards and constructive participant feedback.

### 1.3 Multi-Tenancy & Platform Security
- **REQ-PLT-01**: Multi-tenant data isolation with `Organization`, `Workspace`, and `User` hierarchies.
- **REQ-PLT-02**: Programmatic API access via cryptographically hashed API keys (`ak_live_...`) with fine-grained scopes.
- **REQ-PLT-03**: Token-bucket rate limiting per API key and organization.

### 1.4 Headless B2B Integration & Webhooks
- **REQ-INT-01**: REST API endpoints for async evaluation dispatch (`POST /v1/evaluations`).
- **REQ-INT-02**: Server-Sent Events (SSE) streaming real-time agent thoughts and stage progression.
- **REQ-INT-03**: HMAC-signed webhook delivery to notifying partner platforms upon evaluation completion.

### 1.5 Monetization & Metering
- **REQ-BIL-01**: Metered usage tracking (evaluations processed, sandbox compute seconds, LLM tokens consumed).
- **REQ-BIL-02**: Razorpay payment integration for credit top-ups, order checkout, HMAC-SHA256 signature verification, and automated billing.
- **REQ-BIL-03**: Organization quota enforcement based on subscription tiers (Free, Pro, Enterprise).

### 1.6 Codebase & Rubric RAG Engine (Vector DB)
- **REQ-RAG-01**: Tree-Sitter AST code chunking indexing classes, functions, and API routes into 384-dimensional dense vectors.
- **REQ-RAG-02**: Persistent PostgreSQL `pgvector` index with cosine similarity search for sub-second semantic retrieval.
- **REQ-RAG-03**: Agent semantic search tool enabling Council agents to evaluate large-scale codebases without context window overflow.
- **REQ-RAG-04**: Sponsor track & challenge rule compliance RAG auditor verifying specific SDK usage and deployment artifacts.
- **REQ-RAG-05**: Interactive conversational Q&A endpoint (`POST /v1/evaluations/{id}/chat`) providing evidence-backed answers with file:line citations.

---

## 2. Non-Functional Requirements
- **NFR-PERF-01**: API intake endpoint must return response `< 200ms` by backgrounding evaluation to the task engine.
- **NFR-SEC-01**: Zero host-level privilege escalation or container escape tolerance for untrusted code.
- **NFR-REL-01**: Idempotent and deterministic evaluation replay via pinned Git commit SHAs.
