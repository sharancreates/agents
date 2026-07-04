import os
import sys
import pytest

# Dynamically find the absolute path to the 'agents' directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# Force append both paths to sys.path before loading internal code
if AGENTS_ROOT not in sys.path:
    sys.path.insert(0, AGENTS_ROOT)
if os.path.join(AGENTS_ROOT, "person_2") not in sys.path:
    sys.path.insert(0, os.path.join(AGENTS_ROOT, "person_2"))

from fastapi.testclient import TestClient
# Now it will find app perfectly
from person_2.api.app import app

client = TestClient(app)

def test_api_returns_404_on_invalid_missing_path():
    response = client.post("/api/v1/analyze", json={"directory_path": "invalid/path/location/here"})
    assert response.status_code == 404
    assert "resource reference does not exist" in response.json()["detail"]

def test_api_returns_successful_evaluation_on_valid_dir(tmpdir):
    sample_file = tmpdir.join("api_demo.py")
    sample_file.write("def calculate_sum(a, b):\n    return a + b\n")

    response = client.post("/api/v1/analyze", json={"directory_path": str(tmpdir)})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["total_files_evaluated"] == 1
    assert "metrics" in data
    assert len(data["file_breakdown"]) == 1