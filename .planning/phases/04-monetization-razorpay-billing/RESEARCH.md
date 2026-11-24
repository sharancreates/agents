# Phase 4: Research - Monetization & Razorpay Billing Integration

## 1. Commercial Motivation & Payment Gateway Selection
To generate revenue and monetize AutoJudge as a service, the platform requires automated payment collection, credit balance tracking, and metered usage deductions.

### Why Razorpay?
- **Seamless UPI, Cards, NetBanking, and International Cards**: Industry-standard payment gateway with full support for Indian Rupee (INR) and multi-currency global transactions.
- **Developer-Friendly Webhooks & Signatures**: Cryptographic HMAC-SHA256 payment verification prevents fraudulent balance top-ups.
- **Pay-As-You-Go & Event Passes**: Allows event organizers to buy credits on demand (e.g. ₹999 for 100 evaluations or ₹5,999 for full hackathon licenses) without complex recurring contracts.

---

## 2. Razorpay Payment Architecture & Cryptographic Verification

```
Client / Organizer                        AutoJudge B2B API                         Razorpay Servers
      │                                           │                                        │
      │ 1. POST /v1/billing/orders                │                                        │
      │    (Select 250 credits package)           │                                        │
      ├──────────────────────────────────────────►│                                        │
      │                                           │ 2. Create Order                        │
      │                                           │    (amount=199900 paise, currency=INR) │
      │                                           ├───────────────────────────────────────►│
      │                                           │◄───────────────────────────────────────┤
      │                                           │ 3. Returns order_id: order_xxx         │
      │◄──────────────────────────────────────────┤                                        │
      │ 4. Client displays Razorpay Checkout modal│                                        │
      │    and completes payment                  │                                        │
      │                                           │                                        │
      │ 5. Client submits payment proof:          │                                        │
      │    { order_id, payment_id, signature }    │                                        │
      ├──────────────────────────────────────────►│                                        │
      │                                           │ 6. Verify HMAC-SHA256 signature:       │
      │                                           │    sig = HMAC(order_id|payment_id)     │
      │                                           │ 7. Credit 250 credits to Org Balance   │
      │◄──────────────────────────────────────────┤                                        │
      │ 8. HTTP 200 OK: Credits updated           │                                        │
```

### Signature Verification Formulas:
1. **Frontend Payment Verification**:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{key\_secret}, \text{order\_id} + "|" + \text{payment\_id})$$
   Must match `razorpay_signature` using constant-time comparison (`hmac.compare_digest`).
2. **Webhook Verification**:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{webhook\_secret}, \text{raw\_body})$$
   Matches header `X-Razorpay-Signature`.

---

## 3. Credit Unit Economics & Packages

| Package Name | Price (INR) | Credits Included | Cost Per Evaluation | Target Segment |
| :--- | :--- | :--- | :--- | :--- |
| **Free Starter** | ₹0 | 25 credits on signup | Free | Individual developers testing their projects. |
| **Team / Bootcamp Pack** | ₹499 (49,900 paise) | 100 credits | ₹4.99 / submission | University hackathons, coding bootcamps. |
| **Organizer Pro Pack** | ₹1,999 (199,900 paise)| 500 credits | ₹3.99 / submission | Community hackathons (100–300 teams). |
| **Enterprise Hackathon Pass**| ₹5,999 (599,900 paise)| 2,000 credits | ₹2.99 / submission | Large multi-track hackathons (ETHGlobal, MLH).|

---

## 4. Quota Gating Policy
- Every submission evaluation consumes **1 credit**.
- Before `POST /v1/evaluations` enqueues a job, it checks:
  $$\text{Balance} \ge 1.0$$
- If balance is 0: returns **HTTP 402 Payment Required** with payload:
  ```json
  {
    "error": "INSUFFICIENT_CREDITS",
    "message": "Your organization credit balance is 0. Please top up your balance.",
    "top_up_options": [ ... ]
  }
  ```
- Upon successful evaluation completion in Celery, 1 credit is deducted and a `UsageEvent` is logged into the audit ledger.
