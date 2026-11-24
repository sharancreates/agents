# Project State & Memory

## Project Status
- **Current Milestone**: Commercial Agentic AI & SaaS Transformation
- **Current Phase**: All Milestone Phases Complete (Phases 1, 2, 3, 4, 4.5, and 5 Verified & Closed)
- **Milestone Status**: Commercial Agentic AI & SaaS Transformation COMPLETE
- **Planning Status**: 100% Planned, Executed, and Verified (60/60 passing tests)

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
