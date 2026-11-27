import json
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Base, Organization, ApiKey, Submission, WebhookEndpoint
from api.auth import generate_api_key
from person_2.tests.conftest import TestingSessionLocal

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def seed_portal_org():
    """Sets up an organization, API key, and sample submission for portal tests."""
    db = TestingSessionLocal()
    org = Organization(name="Portal Enterprise Org", slug="portal-org", tier="pro")
    db.add(org)
    db.commit()
    db.refresh(org)
    org_id = org.id

    plain_key, key_rec = generate_api_key(db, org_id, name="Portal Test Key")

    sub = Submission(
        submission_id="sub_portal_001",
        organization_id=org_id,
        team_name="Observability Wizards",
        repo_url="https://github.com/example/observability-app",
        pipeline_status="complete",
        overall_score=89.5,
        synthesis_summary="Strong architecture with verified isolation.",
        agent_traces=[
            {
                "agent_role": "ReconAgent",
                "action": "DISCOVER_STACK",
                "reasoning": "Detected Python 3.10 and FastAPI entrypoint.",
                "timestamp": "2026-11-24T20:00:00Z",
                "payload": {"framework": "FastAPI"}
            },
            {
                "agent_role": "CriticAgent",
                "action": "CALIBRATE_CONSENSUS",
                "reasoning": "Calibrated overall score to 89.5.",
                "timestamp": "2026-11-24T20:01:00Z",
                "payload": {"verdict": "APPROVED"}
            }
        ]
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    db.close()

    return {
        "org_id": org_id,
        "api_key": plain_key,
        "submission_id": "sub_portal_001"
    }

def test_sse_stream_endpoint_headers_and_events(client, seed_portal_org):
    """Verifies that GET /v1/evaluations/{id}/stream streams SSE events with header and token query parameter."""
    headers = {"Authorization": f"Bearer {seed_portal_org['api_key']}"}
    sub_id = seed_portal_org["submission_id"]

    # 1. Request SSE stream using streaming context with Authorization header
    with client.stream("GET", f"/v1/evaluations/{sub_id}/stream", headers=headers) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        lines = []
        for line in resp.iter_lines():
            if line:
                lines.append(line)
            if len(lines) >= 3:
                break

        # Verify SSE structure
        assert any(l.startswith("data: ") for l in lines)
        raw_events = [json.loads(l.replace("data: ", "")) for l in lines if l.startswith("data: ")]

        event_types = [e.get("event") for e in raw_events]
        assert "connected" in event_types

    # 2. Browser EventSource path: authenticate via ?token=... query parameter
    with client.stream("GET", f"/v1/evaluations/{sub_id}/stream?token={seed_portal_org['api_key']}") as resp_query:
        assert resp_query.status_code == 200
        assert "text/event-stream" in resp_query.headers["content-type"]

    # 3. Reject unauthenticated SSE connection
    resp_unauth = client.get(f"/v1/evaluations/{sub_id}/stream")
    assert resp_unauth.status_code == 401

def test_developer_portal_api_keys(client, seed_portal_org):
    """Verifies listing and issuing scoped API keys."""
    headers = {"Authorization": f"Bearer {seed_portal_org['api_key']}"}

    # 1. List existing keys
    list_resp = client.get("/v1/api-keys", headers=headers)
    assert list_resp.status_code == 200
    keys = list_resp.json()
    assert len(keys) >= 1
    assert "key_prefix" in keys[0]

    # 2. Issue new scoped key
    create_resp = client.post(
        "/v1/api-keys",
        json={"name": "CI Deployment Key", "scopes": ["eval:read", "eval:write"]},
        headers=headers
    )
    assert create_resp.status_code == 200
    new_key = create_resp.json()
    assert new_key["api_key"].startswith("ak_live_")
    assert new_key["name"] == "CI Deployment Key"
    assert "warning" in new_key

def test_developer_portal_webhooks(client, seed_portal_org):
    """Verifies webhook registration and retrieval."""
    headers = {"Authorization": f"Bearer {seed_portal_org['api_key']}"}

    # Register webhook
    wh_resp = client.post(
        "/v1/webhooks",
        json={
            "url": "https://hackathon.example.com/webhooks/autojudge",
            "secret": "super_secret_webhook_signing_key_123",
            "events": ["evaluation.completed", "evaluation.failed"]
        },
        headers=headers
    )
    assert wh_resp.status_code == 200
    wh_data = wh_resp.json()
    assert wh_data["url"] == "https://hackathon.example.com/webhooks/autojudge"
    assert "id" in wh_data

    # List webhooks
    list_wh = client.get("/v1/webhooks", headers=headers)
    assert list_wh.status_code == 200
    assert len(list_wh.json()) >= 1

def test_developer_portal_billing_overview(client, seed_portal_org):
    """Verifies that balance and order initiation are accessible for portal UI."""
    headers = {"Authorization": f"Bearer {seed_portal_org['api_key']}"}

    bal_resp = client.get("/v1/billing/balance", headers=headers)
    assert bal_resp.status_code == 200
    data = bal_resp.json()
    assert "balance" in data
    assert len(data["packages_available"]) == 3

    order_resp = client.post(
        "/v1/billing/orders",
        json={"package_id": "pro_500"},
        headers=headers
    )
    assert order_resp.status_code == 201
    assert order_resp.json()["order_id"].startswith("order_")
