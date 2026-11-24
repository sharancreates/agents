import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.models import Base, Organization, Workspace, ApiKey, Submission
from api.auth import get_db, generate_api_key, hash_secret, _RATE_LIMIT_WINDOWS
from api.webhook_service import generate_webhook_signature, verify_webhook_signature
from person_2.tests.conftest import TestingSessionLocal

@pytest.fixture
def seed_tenants():
    db = TestingSessionLocal()
    # Create Organization A
    org_a = Organization(name="Hackathon Org Alpha", slug="org-alpha", tier="free")
    db.add(org_a)
    db.commit()
    db.refresh(org_a)
    org_a_id = org_a.id

    # Issue API key for Org A
    key_a_plain, key_a_rec = generate_api_key(db, org_a.id, name="Org A Key")

    # Create Organization B
    org_b = Organization(name="Hackathon Org Beta", slug="org-beta", tier="pro")
    db.add(org_b)
    db.commit()
    db.refresh(org_b)
    org_b_id = org_b.id

    # Issue API key for Org B
    key_b_plain, key_b_rec = generate_api_key(db, org_b.id, name="Org B Key")

    db.close()

    return {
        "org_a_id": org_a_id,
        "key_a": key_a_plain,
        "org_b_id": org_b_id,
        "key_b": key_b_plain
    }

def test_api_key_auth_success(test_client, seed_tenants):
    """Asserts that requests with valid API keys authenticate successfully."""
    headers = {"Authorization": f"Bearer {seed_tenants['key_a']}"}
    response = test_client.get("/v1/api-keys", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["key_prefix"].startswith("ak_live_")
    # Verify plaintext key is NOT exposed in listing
    assert "api_key" not in data[0]

def test_unauthorized_rejections(test_client):
    """Asserts that missing, malformed, or fake API keys return HTTP 401."""
    # 1. Missing header
    res1 = test_client.get("/v1/api-keys")
    assert res1.status_code == 401

    # 2. Fake key
    res2 = test_client.get("/v1/api-keys", headers={"Authorization": "Bearer ak_live_fake123_invalidkey"})
    assert res2.status_code == 401

def test_multi_tenant_data_isolation(test_client, seed_tenants):
    """
    Asserts strict row-level data segregation:
    Organization B must receive 404 when querying an evaluation owned by Organization A.
    """
    db = TestingSessionLocal()
    # Create a submission belonging to Organization A
    sub = Submission(
        submission_id="sub_tenant_001",
        organization_id=seed_tenants["org_a_id"],
        team_name="Team Alpha 1",
        repo_url="https://github.com/example/repo-alpha",
        pipeline_status="complete",
        overall_score=88.5
    )
    db.add(sub)
    db.commit()
    db.close()

    # 1. Org A queries its own submission -> HTTP 200
    headers_a = {"Authorization": f"Bearer {seed_tenants['key_a']}"}
    res_a = test_client.get("/v1/evaluations/sub_tenant_001", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["evaluation_id"] == "sub_tenant_001"
    assert res_a.json()["organization_slug"] == "org-alpha"

    # 2. Org B queries Org A's submission -> HTTP 404 (strictly segregated)
    headers_b = {"Authorization": f"Bearer {seed_tenants['key_b']}"}
    res_b = test_client.get("/v1/evaluations/sub_tenant_001", headers=headers_b)
    assert res_b.status_code == 404
    assert res_b.json()["detail"] == "Evaluation not found."

def test_rate_limiting_enforcement(test_client, seed_tenants):
    """Asserts that sending requests beyond tier capacity triggers HTTP 429."""
    headers = {"Authorization": f"Bearer {seed_tenants['key_a']}"} # Free tier = 10 req/min

    statuses = []
    for _ in range(12):
        res = test_client.get("/v1/api-keys", headers=headers)
        statuses.append(res.status_code)

    assert 200 in statuses
    assert 429 in statuses
    assert "Retry-After" in res.headers

def test_webhook_signing_and_verification():
    """Verifies HMAC-SHA256 signature generation, validation, and anti-replay protection."""
    secret = "whsec_test_secret_998877"
    raw_payload = '{"event":"evaluation.completed","data":{"score":95.0}}'
    now = int(time.time())

    # 1. Valid signature
    sig_header = generate_webhook_signature(secret, raw_payload, now)
    assert sig_header.startswith(f"t={now},v1=")
    assert verify_webhook_signature(secret, sig_header, raw_payload, tolerance_seconds=300) is True

    # 2. Tampered payload fails
    tampered_payload = '{"event":"evaluation.completed","data":{"score":100.0}}'
    assert verify_webhook_signature(secret, sig_header, tampered_payload) is False

    # 3. Wrong secret fails
    assert verify_webhook_signature("wrong_secret", sig_header, raw_payload) is False

    # 4. Expired timestamp (>300s) fails anti-replay check
    old_timestamp = now - 400
    old_sig = generate_webhook_signature(secret, raw_payload, old_timestamp)
    assert verify_webhook_signature(secret, old_sig, raw_payload, tolerance_seconds=300) is False
