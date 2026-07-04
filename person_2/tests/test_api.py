import os
import sys
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

if AGENTS_ROOT not in sys.path:
    sys.path.insert(0, AGENTS_ROOT)
if os.path.join(AGENTS_ROOT, "person_2") not in sys.path:
    sys.path.insert(0, os.path.join(AGENTS_ROOT, "person_2"))

from fastapi.testclient import TestClient
from person_2.api.app import app

client = TestClient(app)

def test_api_returns_404_on_invalid_missing_path():
    response = client.post("/api/v1/analyze", json={"directory_path": "invalid/path/location/here"})
    assert response.status_code == 404

def test_api_returns_successful_evaluation_on_valid_dir(tmpdir):
    sample_file = tmpdir.join("api_demo.py")
    sample_file.write("def calculate_sum(a, b):\n    return a + b\n")
    response = client.post("/api/v1/analyze", json={"directory_path": str(tmpdir)})
    assert response.status_code == 200

# --- NEW: Async Architecture Processing Assertions ---
def test_async_endpoint_lifecycle_flow(tmpdir):
    sample_file = tmpdir.join("async_demo.py")
    sample_file.write("print('Async Worker Test Run')\n")

    # 1. Trigger async request
    response = client.post("/api/v1/analyze/async", json={"directory_path": str(tmpdir)})
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    task_id = data["task_id"]

    # 2. Query status lookup route immediately
    status_response = client.get(f"/api/v1/tasks/{task_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] in ("PENDING", "PROCESSING", "COMPLETED")