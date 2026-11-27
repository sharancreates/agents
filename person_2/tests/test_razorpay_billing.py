import json
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api import models
from api.models import (
    Base, Organization, ApiKey, OrganizationCredit, PaymentOrder, UsageEvent, Submission
)
from api.auth import get_db, generate_api_key, _RATE_LIMIT_WINDOWS
from api.billing_service import BillingService, CREDIT_PACKAGES
from api.razorpay_client import (
    generate_payment_signature,
    generate_webhook_signature,
    RAZORPAY_KEY_SECRET,
    RAZORPAY_WEBHOOK_SECRET
)
from person_2.tests.conftest import TestingSessionLocal

@pytest.fixture
def seed_org():
    db = TestingSessionLocal()
    org = Organization(name="FinTech Hackathon Org", slug="fintech-org", tier="pro")
    db.add(org)
    db.commit()
    db.refresh(org)
    org_id = org.id

    plain_key, _ = generate_api_key(db, org.id, name="Billing Test Key")
    db.close()
    return {"org_id": org_id, "api_key": plain_key}

def test_credit_balance_provisioning(client, seed_org):
    """Verifies that accessing balance initializes 25 free credits automatically."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}
    resp = client.get("/v1/billing/balance", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["organization_id"] == seed_org["org_id"]
    assert data["balance"] == 25.0
    assert len(data["packages_available"]) == 3

def test_create_order_valid_and_invalid_package(client, seed_org):
    """Verifies Razorpay order creation for valid packages and rejection for invalid ones."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}
    
    # Valid package
    resp = client.post(
        "/v1/billing/orders",
        json={"package_id": "starter_100"},
        headers=headers
    )
    assert resp.status_code == 201
    order_data = resp.json()
    assert order_data["order_id"].startswith("order_")
    assert order_data["amount_paise"] == 49900
    assert order_data["amount_inr"] == 499.0
    assert order_data["credits_to_grant"] == 100

    # Invalid package
    bad_resp = client.post(
        "/v1/billing/orders",
        json={"package_id": "nonexistent_pack"},
        headers=headers
    )
    assert bad_resp.status_code == 400

def test_verify_payment_valid_signature(client, seed_org):
    """Verifies HMAC signature validation and atomic credit grant upon payment completion."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}

    # Step 1: Create Order
    create_resp = client.post(
        "/v1/billing/orders",
        json={"package_id": "pro_500"},
        headers=headers
    )
    assert create_resp.status_code == 201
    order_id = create_resp.json()["order_id"]
    payment_id = "pay_test_pro_12345"

    # Step 2: Generate valid HMAC signature
    valid_sig = generate_payment_signature(order_id, payment_id, RAZORPAY_KEY_SECRET)

    # Step 3: Verify payment
    verify_resp = client.post(
        "/v1/billing/verify-payment",
        json={
            "order_id": order_id,
            "payment_id": payment_id,
            "signature": valid_sig
        },
        headers=headers
    )
    assert verify_resp.status_code == 200
    res = verify_resp.json()
    assert res["status"] == "success"
    assert res["credits_granted"] == 500
    # 25 free + 500 granted = 525.0
    assert res["new_balance"] == 525.0

def test_verify_payment_invalid_signature_rejected(client, seed_org):
    """Verifies that tampered or forged signatures are strictly rejected with HTTP 400."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}

    create_resp = client.post(
        "/v1/billing/orders",
        json={"package_id": "starter_100"},
        headers=headers
    )
    order_id = create_resp.json()["order_id"]

    forged_sig = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    verify_resp = client.post(
        "/v1/billing/verify-payment",
        json={
            "order_id": order_id,
            "payment_id": "pay_fraud_999",
            "signature": forged_sig
        },
        headers=headers
    )
    assert verify_resp.status_code == 400
    assert "Invalid payment signature" in verify_resp.json()["detail"]

def test_double_spend_replay_rejected(client, seed_org):
    """Verifies that an already claimed payment_id cannot be reused (replay prevention)."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}

    # Order 1
    ord1 = client.post("/v1/billing/orders", json={"package_id": "starter_100"}, headers=headers).json()["order_id"]
    payment_id = "pay_unique_replay_token"
    sig1 = generate_payment_signature(ord1, payment_id, RAZORPAY_KEY_SECRET)

    res1 = client.post(
        "/v1/billing/verify-payment",
        json={"order_id": ord1, "payment_id": payment_id, "signature": sig1},
        headers=headers
    )
    assert res1.status_code == 200

    # Attempt replay with Order 2 using identical payment_id
    ord2 = client.post("/v1/billing/orders", json={"package_id": "starter_100"}, headers=headers).json()["order_id"]
    sig2 = generate_payment_signature(ord2, payment_id, RAZORPAY_KEY_SECRET)
    replay_res = client.post(
        "/v1/billing/verify-payment",
        json={"order_id": ord2, "payment_id": payment_id, "signature": sig2},
        headers=headers
    )
    assert replay_res.status_code == 400
    assert "already been credited" in replay_res.json()["detail"]

def test_razorpay_webhook_event_processing(client, seed_org):
    """Verifies webhook signature validation and payment event ingestion."""
    db = TestingSessionLocal()
    order = models.PaymentOrder(
        organization_id=seed_org["org_id"],
        package_id="starter_100",
        razorpay_order_id="order_wh_test_999",
        amount_paise=49900,
        currency="INR",
        credits_to_grant=100,
        status="created"
    )
    db.add(order)
    db.commit()
    db.close()

    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_wh_captured_001",
                    "order_id": "order_wh_test_999",
                    "amount": 49900,
                    "status": "captured"
                }
            }
        }
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    valid_sig = generate_webhook_signature(raw_body, RAZORPAY_WEBHOOK_SECRET)

    # Valid webhook request
    resp = client.post(
        "/v1/billing/razorpay-webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": valid_sig}
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is True

    # Bad signature
    bad_resp = client.post(
        "/v1/billing/razorpay-webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "invalid_signature"}
    )
    assert bad_resp.status_code == 400

def test_quota_gating_blocks_when_zero_credits(client, seed_org):
    """Verifies HTTP 402 Payment Required is returned when credit balance is depleted."""
    # Deplete balance to 0
    db = TestingSessionLocal()
    acc = BillingService.get_or_create_credit_account(db, seed_org["org_id"])
    acc.balance = 0.0
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}
    eval_resp = client.post(
        "/v1/evaluations",
        json={"repo_url": "https://github.com/test/repo"},
        headers=headers
    )
    assert eval_resp.status_code == 402
    assert eval_resp.json()["detail"]["error"] == "INSUFFICIENT_CREDITS"

def test_quota_admission_and_metered_deduction(client, seed_org):
    """Verifies that evaluations are admitted when credits exist and deductions update ledger."""
    headers = {"Authorization": f"Bearer {seed_org['api_key']}"}

    # Org starts with 25 credits, evaluation is accepted and credit is reserved upfront
    with patch("api.v1_endpoints.process_submission_task.delay"):
        eval_resp = client.post(
            "/v1/evaluations",
            json={"repo_url": "https://github.com/test/repo", "team_name": "Quota Test Team"},
            headers=headers
        )
    assert eval_resp.status_code == 202
    submission_id = eval_resp.json()["evaluation_id"]

    # Check updated balance (atomically decremented to 24.0 upon evaluation admission)
    bal_resp = client.get("/v1/billing/balance", headers=headers)
    assert bal_resp.json()["balance"] == 24.0
    assert bal_resp.json()["total_consumed"] == 1.0

    # Check usage audit ledger
    usage_resp = client.get("/v1/billing/usage", headers=headers)
    assert usage_resp.status_code == 200
    events = usage_resp.json()
    assert len(events) >= 1
    assert events[0]["submission_id"] == submission_id
    assert events[0]["credits_deducted"] == 1.0
