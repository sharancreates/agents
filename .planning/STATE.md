# Project State & Memory

## Project Status
- **Current Milestone**: Commercial Agentic AI & SaaS Transformation
- **Current Phase**: All Milestone Phases Complete (Phases 1, 2, 3, 4, 4.5, and 5 Verified & Closed)
- **Milestone Status**: Commercial Agentic AI & SaaS Transformation COMPLETE
- **Planning Status**: 100% Planned, Executed, and Verified (63/63 passing tests)

## PR #14 Aligned Specification
- **Title**: `feat: AutoJudge B2B Platform, Multi-Agent Deliberation Council, Sandbox MicroVM Isolation, & Developer Portal`
- **Scope**: Replaces legacy CLI/action prototypes with the comprehensive AutoJudge enterprise architecture:
  1. **Sandbox Execution Engine**: Multi-language runtime isolation (Docker `--network none`, least-privilege UID 1000, read-only rootfs, E2B Cloud MicroVM provider).
  2. **Multi-Agent Deliberation Council**: 6-agent evaluative consensus (Recon, dynamic QA synthesis, Quality AST complexity, Git Forensics, Critic calibration, and Feedback dossier).
  3. **B2B API & Multi-Tenancy**: Organization row-level isolation, scoped `ak_live_` API keys with rate-limiting, and signed HMAC-SHA256 webhook callbacks.
  4. **Razorpay Monetization & Quota Gating**: Atomic credit deductions, order management, integer paise pricing, and cryptographically verified HMAC signatures.
  5. **AST Codebase RAG & Copilot**: pgvector/cosine retrieval, sponsor compliance auditing, and contextual code citation generation.
  6. **Enterprise Portal & Observability**: Real-time Server-Sent Events (SSE) telemetry stream, Developer API/Webhook/Billing console, and Judge Copilot interface.

## Architecture Baseline
- **Backend**: FastAPI (`api/main.py`), SQLAlchemy ORM (`api/models.py`), Celery (`orchestrator/celery_app.py`)
- **Queue/Broker**: Redis (`redis://localhost:6379/0`)
- **Databases**: PostgreSQL (`submissions_db` on port 5433) + `pgvector`
- **Frontend**: React 19 + Vite (`frontend/`) - Production bundle compiled cleanly
- **Sandbox Architecture**: Complete & Operational (`sandbox/` module - microVM isolation, network block, cgroup caps)
- **Agent Council Engine**: Complete & Operational (`agents/council/` module - Recon, QA, Quality, Forensics, Critic, Feedback)
- **B2B Multi-Tenant Platform**: Complete & Operational (Scoped `ak_live_` API keys, HMAC-signed webhooks, tenant segregation)
- **Billing Architecture**: Complete & Operational (Razorpay orders, HMAC-SHA256 verification, integer paise precision, quota gating)
- **RAG & Vector Search**: Complete & Operational (`CodeEmbedding`, AST chunking, 384-d dense vectors, cosine retrieval, sponsor compliance auditor, Judge Copilot API)
- **Enterprise Portal & Observability**: Complete & Operational (Server-Sent Events streaming, Developer & Billing Console at `/developer`, Agent Deliberation Console, Rubric Customizer, Judge Copilot drawer)

## Known Decisions & Constraints
- **Payment Gateway**: Mandated **Razorpay** with integer paise arithmetic and SHA-256 HMAC signature verification.
- **RAG Architecture**: AST chunking with line-numbered citations; hybrid pgvector/SQLite cosine similarity; 384-dimensional unit vectors with deterministic test fallback.
- **Observability**: Server-Sent Events (SSE) for unidirectional agent telemetry with polling fallback.
- **Security & Multi-Tenancy**: Zero plaintext API keys or webhook secrets stored; constant-time SHA-256 validation.
- **Strict Data Segregation**: Row-level organization scoping prevents cross-tenant data leaks.
- **Webhook Delivery**: Anti-replay timestamping and HMAC-SHA256 signatures for safe partner consumption.
