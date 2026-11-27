# Phase 4: Verification Protocol - Razorpay Monetization & Metered Billing

## 1. Test Verification Command
Executed across the entire test suite:
```powershell
pytest person_2/tests/ -o pythonpath=".venv/Lib/site-packages ." -v
```
**Result**: `49 passed, 2 warnings in 12.03s` (100% pass rate).

---

## 2. Acceptance Criteria Checklist

### Functional Criteria
- [x] **Data Models**:
  - `OrganizationCredit` correctly persists credit balances and historical totals.
  - `PaymentOrder` tracks order IDs, payment IDs, integer paise amounts, and payment status.
  - `UsageEvent` provides an immutable audit trail of credit consumption.
- [x] **Razorpay Client & Cryptography**:
  - Orders are initiated with correct paise amounts (e.g. 49900 paise for 100 credits).
  - HMAC-SHA256 signature verification accepts authentic signatures.
  - HMAC-SHA256 rejects tampered or forged signatures.
  - Webhook signatures (`X-Razorpay-Signature`) are verified against raw request bodies.
  - Simulation client activates transparently when keys are absent.
- [x] **Billing Service**:
  - Credit accounts are initialized with default starter credits (25 credits).
  - Orders can be created for all supported tiers (`starter_100`, `pro_500`, `enterprise_2000`).
  - Double-spend attempts with duplicate `payment_id` are rejected.
  - Credit balance is atomically incremented upon verification.
  - Credits are atomically deducted upon evaluation completion.
- [x] **REST Endpoints**:
  - `GET /v1/billing/balance`: Returns current balance and credit packages.
  - `POST /v1/billing/orders`: Returns created Razorpay order details.
  - `POST /v1/billing/verify-payment`: Verifies payment and updates balance.
  - `POST /v1/billing/razorpay-webhook`: Processes webhook payment events.
  - `GET /v1/billing/usage`: Returns historical usage records.
- [x] **Quota Gating**:
  - When an organization has `balance == 0`, `POST /v1/evaluations` returns **HTTP 402 Payment Required**.
  - When an organization has `balance >= 1`, `POST /v1/evaluations` accepts the job (**HTTP 202 Accepted**).
  - Background worker deducts 1 credit upon evaluation finish and creates a `UsageEvent`.

---

## 3. Regression Invariants
- All 49 tests across:
  - `person_2/tests/test_sandbox_security.py` (6 tests)
  - `person_2/tests/test_agent_council.py` (7 tests)
  - `person_2/tests/test_b2b_api.py` (5 tests)
  - `person_2/tests/test_razorpay_billing.py` (8 tests)
  - Core functionality and rule tests (23 tests)
  are 100% passing with 0 failures or regressions.
