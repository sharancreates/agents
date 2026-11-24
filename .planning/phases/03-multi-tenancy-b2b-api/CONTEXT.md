# Phase 3: Context & Scope

## 1. Phase Objective
Build the **Multi-Tenant B2B Developer Platform** that enables external platforms (hackathons, universities, hiring software) to securely interact with AutoJudge via API keys, receive real-time evaluations, manage scoped workspaces, and consume signed HMAC-SHA256 webhooks.

---

## 2. Scope Boundaries

### In Scope:
- **Relational Models (`api/models.py`)**:
  - `Organization`: Multi-tenant boundary with tier tracking (`free`, `pro`, `enterprise`).
  - `Workspace`: Scoped environments for specific hackathons or cohorts.
  - `ApiKey`: Cryptographically hashed keys with capability scopes.
  - `WebhookEndpoint`: Partner notification endpoints with HMAC secret hashing.
  - `Submission` updates: Association with `organization_id` and `workspace_id`.
- **Authentication & Rate Limiting (`api/auth.py`)**:
  - Fast SHA-256 API key authentication dependency.
  - Sliding-window / token-bucket rate limiter per organization tier.
- **Headless B2B Developer Endpoints (`api/v1_endpoints.py`)**:
  - `POST /v1/evaluations`: Enqueues an evaluation request with custom challenge prompts, rubrics, and optional callback URLs.
  - `GET /v1/evaluations/{id}`: Returns status, composite scores, and participant commentary.
  - `GET /v1/evaluations/{id}/traces`: Returns detailed agent audit logs for explainability.
  - `POST /v1/api-keys`: Issues and revokes API keys.
  - `POST /v1/webhooks`: Registers partner webhook callbacks.
- **HMAC Webhook Dispatch Engine (`api/webhook_service.py`)**:
  - Signs payloads with HMAC-SHA256 and timestamps.
  - Dispatches results asynchronously on evaluation completion.
- **Test Matrix (`person_2/tests/test_b2b_api.py`)**:
  - Comprehensive unit and integration test suite verifying authentication, cross-tenant data isolation, rate limiting, and webhook signatures.

### Out of Scope:
- Stripe checkout sessions and payment webhooks (deferred to Phase 4).
- Metered credit deduction and overage billing (deferred to Phase 4).
- Frontend UI dashboard for key management (deferred to Phase 5).

---

## 3. Security & Isolation Invariants
1. **Strict Data Segregation**: API keys belonging to Organization A can NEVER query, mutate, or see submissions from Organization B.
2. **Zero Plaintext Secrets in DB**: API keys and webhook secrets are hashed with SHA-256 prior to insertion.
3. **Constant-Time Verification**: API key and webhook secret verification must use `hmac.compare_digest` to prevent timing attacks.
