# Phase 4 Plan: Monetization Engine & Metered Billing (Razorpay)

## Goal
Implement a commercial, production-ready monetization engine powered by **Razorpay** that supports prepaid credit packages, cryptographic HMAC-SHA256 payment signature verification, automated credit granting, metered usage deductions, and HTTP 402 quota gating.

---

## 1. Context & Architecture

- **Payment Gateway**: Razorpay (UPI, NetBanking, Cards, Multi-Currency).
- **Monetary Unit**: Integer paise (1 INR = 100 paise) to eliminate floating-point calculation errors.
- **Credit Economics**: 1 submission evaluation = 1 credit.
  - Free Starter: 25 initial credits.
  - Team / Bootcamp Pack: ₹499 (49,900 paise) -> 100 credits.
  - Organizer Pro Pack: ₹1,999 (199,900 paise) -> 500 credits.
  - Enterprise Hackathon Pass: ₹5,999 (599,900 paise) -> 2,000 credits.
- **Cryptographic Security**:
  - Payment signature: HMAC-SHA256(key_secret, order_id + "|" + payment_id)
  - Webhook signature: HMAC-SHA256(webhook_secret, raw_body)
- **Environments**: Live credentials support with an automatic high-fidelity simulation engine for CI/test and offline environments.

---

## 2. Task Breakdown

### Task 1: [TRACER SLICE] Relational Models & Razorpay Client
- **Files**:
  - `api/models.py`:
    - `OrganizationCredit`: `id`, `organization_id` (unique foreign key), `balance` (Float/Integer), `total_purchased`, `total_consumed`, `updated_at`.
    - `PaymentOrder`: `id`, `organization_id`, `razorpay_order_id` (unique index), `razorpay_payment_id` (unique index, nullable), `amount_paise`, `currency`, `credits_to_grant`, `status` (`created`, `paid`, `failed`), `created_at`, `paid_at`.
    - `UsageEvent`: `id`, `organization_id`, `submission_id`, `credits_deducted`, `reason`, `created_at`.
  - `api/razorpay_client.py`:
    - `RazorpayClient`: Wrapper supporting `.orders.create(amount, currency, receipt, notes)`.
    - `verify_payment_signature(order_id, payment_id, signature, key_secret) -> bool`: Constant-time HMAC comparison.
    - `verify_webhook_signature(raw_body, signature, webhook_secret) -> bool`: Webhook HMAC validation.
    - `SimulatedRazorpayClient`: Deterministic mock for local testing and CI when keys are not configured.

### Task 2: Billing Management Service
- **Files**:
  - `api/billing_service.py`:
    - `get_or_create_credit_account(db, org_id) -> OrganizationCredit`: Ensures default credit allotment for new orgs.
    - `create_order(db, org_id, package_id) -> PaymentOrder`: Validates package, creates Razorpay order, persists record.
    - `process_successful_payment(db, org_id, order_id, payment_id, signature) -> OrganizationCredit`:
      - Replay check: ensures `payment_id` has never been credited.
      - Verifies HMAC signature.
      - Atomically transitions order status to `paid` and increments credit balance.
    - `has_sufficient_credits(db, org_id, required_credits=1) -> bool`: Checks if organization can initiate evaluation.
    - `deduct_credit(db, org_id, submission_id, credits=1) -> bool`: Decrements balance and logs an immutable `UsageEvent`.
    - `get_usage_history(db, org_id, limit=50) -> List[UsageEvent]`.

### Task 3: REST API Billing Endpoints & Routing
- **Files**:
  - `api/billing_endpoints.py`:
    - `GET /v1/billing/balance`: Returns available balance, tier, and pricing packages.
    - `POST /v1/billing/orders`: Body `{ "package_id": "pro_500" }` -> returns `{ "order_id", "amount", "currency", "key_id" }`.
    - `POST /v1/billing/verify-payment`: Body `{ "order_id", "payment_id", "signature" }` -> verifies & credits account.
    - `POST /v1/billing/razorpay-webhook`: Validates `X-Razorpay-Signature` and processes `payment.captured` / `order.paid`.
    - `GET /v1/billing/usage`: Paginated list of usage ledger events.
  - `api/main.py`:
    - Mount `billing_router` into FastAPI application.

### Task 4: Quota Gating & Metered Usage Hook
- **Files**:
  - `api/v1_endpoints.py`:
    - In `create_evaluation`: Call `billing_service.has_sufficient_credits(db, org.id, 1)`.
    - If false, raise `HTTPException(status_code=402, detail={"error": "INSUFFICIENT_CREDITS", "message": "Credit balance is zero. Please top up to continue evaluations."})`.
  - `orchestrator/celery_app.py`:
    - When `process_submission_task` finishes evaluation, call `billing_service.deduct_credit(db, org_id, sub.submission_id)`.
    - Ensure failed tasks or cancellations are handled properly (no deduction on system failure).

### Task 5: Automated Verification Suite & Regression Testing
- **Files**:
  - `person_2/tests/test_razorpay_billing.py`:
    - Test order creation and package pricing integrity.
    - Test valid HMAC signature verification and credit fulfillment.
    - Test invalid / forged signature rejection.
    - Test double-spend replay protection (attempting to submit the same `payment_id` twice).
    - Test webhook payload handling with valid and forged webhook signatures.
    - Test HTTP 402 quota gating when credits are depleted.
    - Test evaluation admission when credits are available.
    - Test credit balance deduction and `UsageEvent` recording.
  - Regression check: Ensure all existing 41 tests in `person_2/tests/` remain 100% green.

---

## 3. Risk Mitigation & Invariants
- **Floating-point drift**: All amounts in `PaymentOrder` stored as integer paise.
- **Double credit grants**: Unique DB index on `razorpay_payment_id` + transaction lock on `PaymentOrder`.
- **Offline / CI testing**: Fallback simulation ensures zero test failures even without live Razorpay API keys.
