# Phase 3: Implementation Plan - Multi-Tenancy, B2B Developer API & Webhooks

```
Mode: tracer-first
Status: planned
Target: 03-multi-tenancy-b2b-api
```

---

## Task Breakdown

### Task 1: [TRACER SLICE] Multi-Tenant Relational Schema & API Key Engine
**Goal**: Establish organizational boundaries and secure API key authentication.
- **Files to create/modify**:
  - `api/models.py`:
    - Add `Organization` (`id`, `name`, `slug`, `tier`, `created_at`).
    - Add `Workspace` (`id`, `organization_id`, `name`, `slug`, `default_rubric`, `created_at`).
    - Add `ApiKey` (`id`, `organization_id`, `name`, `key_prefix`, `key_hash`, `scopes`, `is_active`, `last_used_at`, `created_at`).
    - Add `WebhookEndpoint` (`id`, `organization_id`, `url`, `secret_hash`, `events`, `is_active`, `created_at`).
    - Update `Submission` with `organization_id` and `workspace_id`.
  - `api/auth.py`:
    - `generate_api_key()`: Cryptographically generates `ak_live_{prefix}_{secret}`, hashes with SHA-256, and returns plaintext once.
    - `get_api_org()`: FastAPI header dependency resolving and validating API keys using constant-time hash comparisons.
- **Verification**: Run tracer test issuing an API key, validating it, and verifying that invalid/tampered keys return HTTP 401.

---

### Task 2: Tiered Rate Limiting & Access Governance
**Goal**: Enforce throughput ceilings per organization tier to protect infrastructure and enable commercial monetization tiers.
- **Files to create/modify**:
  - `api/auth.py`:
    - `RateLimiter`: Sliding window rate limiter tracking request timestamps in Redis (or in-memory cache fallback).
    - Tier policies: Free (10 req/min), Pro (60 req/min), Enterprise (300 req/min).
    - Emits standard rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Verification**: Test that exceeding tier quotas raises HTTP 429 Too Many Requests with correct retry headers.

---

### Task 3: Headless B2B Developer Endpoints (`/v1/evaluations`)
**Goal**: Expose a clean, developer-friendly REST API for third-party platforms to trigger and manage evaluations.
- **Files to create/modify**:
  - `api/v1_endpoints.py`:
    - `POST /v1/evaluations`: Intake endpoint accepting `{ repo_url, challenge_prompt, rubric_weights, webhook_url }`, scoped to caller's organization.
    - `GET /v1/evaluations/{id}`: Retrieves evaluation state, scores, and participant commentary (enforces strict tenant isolation).
    - `GET /v1/evaluations/{id}/traces`: Retrieves agent audit traces.
    - `POST /v1/api-keys` & `DELETE /v1/api-keys/{id}`: Key lifecycle management.
    - `POST /v1/webhooks`: Partner webhook endpoint registration.
  - `api/main.py`:
    - Mount `/v1` router onto the primary FastAPI app.
- **Verification**: Use TestClient to test evaluation submission, tenant isolation, and key revocation.

---

### Task 4: HMAC Webhook Dispatch Engine
**Goal**: Automatically dispatch signed event notifications to partner platforms when evaluations finish.
- **Files to create/modify**:
  - `api/webhook_service.py`:
    - `sign_payload()`: Computes HMAC-SHA256 signature over `{timestamp}.{raw_body}`.
    - `verify_signature()`: Verification helper for partner SDKs.
    - `dispatch_webhook_event()`: Dispatches HTTP POST with exponential backoff retry.
  - `orchestrator/celery_app.py`:
    - Trigger webhook event upon pipeline completion or failure.
- **Verification**: Test webhook signing, delivery payload formatting, and signature verification.

---

### Task 5: End-to-End Multi-Tenancy & B2B Test Suite
**Goal**: Verify all multi-tenant isolation, security, and developer API contracts.
- **Files to create/modify**:
  - `person_2/tests/test_b2b_api.py`:
    - Test API key creation, prefix masking, and authentication.
    - Test cross-tenant data segregation (Org A cannot query Org B's evaluations).
    - Test rate limit enforcement (HTTP 429).
    - Test webhook generation and HMAC verification.
- **Verification**: Run `pytest person_2/tests/test_b2b_api.py -v` and confirm 100% pass rate.
