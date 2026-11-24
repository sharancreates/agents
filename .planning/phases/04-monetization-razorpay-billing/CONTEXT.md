# Phase 4: Context & Scope

## 1. Phase Objective
Integrate a production **Monetization Engine powered by Razorpay** featuring prepaid credit packages, cryptographic payment signature verification, automated credit granting, metered usage deductions, and HTTP 402 quota gating.

---

## 2. Scope Boundaries

### In Scope:
- **Billing Data Models (`api/models.py`)**:
  - `OrganizationCredit`: Current credit balance, total purchased, total consumed.
  - `PaymentOrder`: Razorpay order records, payment IDs, amounts in paise, currencies, and payment statuses.
  - `UsageEvent`: Ledger of credit consumption per submission evaluation.
- **Razorpay Client & Verification Engine (`api/razorpay_client.py`)**:
  - Razorpay Orders API client for creating checkout orders.
  - HMAC-SHA256 signature verification for client payments and webhooks.
  - Seamless test simulation mode when `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` are not configured.
- **Credit & Billing Management Service (`api/billing_service.py`)**:
  - Balance retrieval, order initiation, payment confirmation, and credit deduction.
- **REST Endpoints (`api/billing_endpoints.py`)**:
  - `GET /v1/billing/balance`: View available credits and tier.
  - `POST /v1/billing/orders`: Initiate Razorpay checkout order for a credit package.
  - `POST /v1/billing/verify-payment`: Verify payment signature and credit organization account.
  - `POST /v1/billing/razorpay-webhook`: Asynchronous webhook handler for `payment.captured`.
  - `GET /v1/billing/usage`: Audit trail of credit consumption.
- **Quota Gating & Usage Enforcement**:
  - Update `api/v1_endpoints.py` to block evaluation requests with HTTP 402 if credit balance < 1.
  - Update `orchestrator/celery_app.py` to deduct credit upon successful completion.
- **Verification Suite**:
  - `person_2/tests/test_razorpay_billing.py` testing the complete payment lifecycle, HMAC verification, and quota gating.

### Out of Scope:
- Stripe integration (replaced with Razorpay as explicitly requested by user).
- Front-end checkout modal UI (deferred to Phase 5).
- AST Codebase RAG and vector retrieval (deferred to Phase 4.5).

---

## 3. Financial Invariants
1. **Paise Precision**: All monetary values are processed and stored as integer paise (e.g. ₹499 = 49900 paise) to prevent floating-point rounding errors.
2. **Double-Spend Prevention**: A `razorpay_payment_id` cannot be used more than once; replay attempts are rejected.
3. **Transaction Atomicity**: Credit balance updates and `PaymentOrder` state transitions must execute within a single database transaction.
