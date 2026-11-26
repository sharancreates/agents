import os
import math
import tempfile
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import (
    Base, Organization, ApiKey, Submission, CodeEmbedding, RubricRequirement
)
from api.auth import generate_api_key
from agents.rag.chunker import ASTCodeChunker
from agents.rag.embedder import DenseEmbedder
from agents.rag.vector_store import VectorStore, cosine_similarity
from agents.rag.indexer import CodebaseIndexer
from agents.rag.compliance import SponsorComplianceAuditor
from person_2.tests.conftest import TestingSessionLocal

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def seed_rag_submission():
    """Sets up an organization and submission record in the test database."""
    db = TestingSessionLocal()
    org = Organization(name="AI Hackathon Org", slug="ai-hack-org", tier="enterprise")
    db.add(org)
    db.commit()
    db.refresh(org)
    org_id = org.id

    plain_key, _ = generate_api_key(db, org.id, name="RAG Test Key")

    sub = Submission(
        submission_id="sub_rag_001",
        organization_id=org_id,
        team_name="Vector Pioneers",
        repo_url="https://github.com/example/rag-demo",
        pipeline_status="complete",
        overall_score=92.0
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    db.close()

    return {
        "org_id": org_id,
        "api_key": plain_key,
        "submission_id": "sub_rag_001"
    }

def test_ast_code_chunker():
    """Verifies Python AST chunking extracts functions, classes, routes, and line numbers."""
    sample_code = (
        'import os\n'
        'from fastapi import APIRouter\n'
        '\n'
        'router = APIRouter()\n'
        '\n'
        '@router.get("/v1/health")\n'
        'def health_check():\n'
        '    """Returns service health."""\n'
        '    return {"status": "ok"}\n'
        '\n'
        'class DatabaseManager:\n'
        '    """Manages persistent connections."""\n'
        '    def connect(self):\n'
        '        return True\n'
        '\n'
        'def compute_metrics(x, y):\n'
        '    return x + y\n'
    )

    chunks = ASTCodeChunker.chunk_python_source(sample_code, "api/routes.py")
    assert len(chunks) >= 3

    symbols = {c["symbol_name"]: c for c in chunks}
    assert "health_check" in symbols
    assert symbols["health_check"]["symbol_type"] == "route"
    assert symbols["health_check"]["start_line"] == 6

    assert "DatabaseManager" in symbols
    assert symbols["DatabaseManager"]["symbol_type"] == "class"

    assert "compute_metrics" in symbols
    assert symbols["compute_metrics"]["symbol_type"] == "function"

def test_dense_embedder_properties():
    """Verifies that 384-d normalized embeddings exhibit semantic similarity."""
    text1 = "Google Gemini multimodal live streaming API"
    text2 = "Gemini AI model client for generation"
    text3 = "Homemade chocolate chip cookie recipe"

    v1 = DenseEmbedder.embed_text(text1)
    v2 = DenseEmbedder.embed_text(text2)
    v3 = DenseEmbedder.embed_text(text3)

    assert len(v1) == 384
    assert len(v2) == 384
    assert len(v3) == 384

    # Assert unit norm (L2 = 1.0)
    norm1 = math.sqrt(sum(x * x for x in v1))
    assert math.isclose(norm1, 1.0, rel_tol=1e-3)

    sim_related = cosine_similarity(v1, v2)
    sim_unrelated = cosine_similarity(v1, v3)

    assert sim_related > sim_unrelated

def test_vector_store_persistence_and_search():
    """Verifies storing embeddings and retrieving nearest neighbors with citations."""
    db = TestingSessionLocal()
    submission_id = "sub_test_vs_01"

    chunks = [
        {
            "file_path": "services/auth.py",
            "symbol_name": "verify_api_key",
            "symbol_type": "function",
            "start_line": 10,
            "end_line": 25,
            "content": "def verify_api_key(token): return hmac.compare_digest(hash(token), expected)",
            "embedding": DenseEmbedder.embed_text("authentication API key verification token HMAC")
        },
        {
            "file_path": "services/payments.py",
            "symbol_name": "create_razorpay_order",
            "symbol_type": "function",
            "start_line": 30,
            "end_line": 45,
            "content": "def create_razorpay_order(amount): return razorpay_client.orders.create(amount)",
            "embedding": DenseEmbedder.embed_text("razorpay payment order checkout amount paise")
        }
    ]

    stored = VectorStore.store_embeddings(db, submission_id, chunks)
    assert stored == 2

    # Query for payment logic
    query_vec = DenseEmbedder.embed_text("razorpay checkout order payment")
    results = VectorStore.similarity_search(db, submission_id, query_vec, top_k=1)

    assert len(results) == 1
    top = results[0]
    assert top["symbol_name"] == "create_razorpay_order"
    assert top["citation"] == "services/payments.py:30-45"
    assert top["score"] > 0.40

    db.close()

def test_codebase_indexer_directory():
    """Verifies directory indexing extracts files, computes embeddings, and stores records."""
    db = TestingSessionLocal()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample files
        f1 = os.path.join(tmpdir, "main.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("def run():\n    print('hello world')\n")

        f2 = os.path.join(tmpdir, "client.js")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("export function connect() { return true; }\n")

        # Create ignored dir
        ignored = os.path.join(tmpdir, "node_modules")
        os.makedirs(ignored)
        with open(os.path.join(ignored, "bad.js"), "w") as f:
            f.write("var x = 1;")

        res = CodebaseIndexer.index_submission(db, "sub_tmp_001", tmpdir)
        assert res["chunks_indexed"] >= 2
        assert res["status"] == "complete"

    db.close()

def test_sponsor_compliance_auditor():
    """Verifies that the auditor identifies compliant vs non-compliant requirements."""
    db = TestingSessionLocal()
    submission_id = "sub_comp_001"

    # Index razorpay and redis chunks
    chunks = [
        {
            "file_path": "billing.py",
            "symbol_name": "verify_payment",
            "symbol_type": "function",
            "start_line": 5,
            "end_line": 20,
            "content": "from razorpay import Client\nclient.orders.create(amount_paise=49900)",
            "embedding": DenseEmbedder.embed_text("razorpay client orders create amount paise payment")
        },
        {
            "file_path": "queue.py",
            "symbol_name": "init_redis",
            "symbol_type": "function",
            "start_line": 1,
            "end_line": 10,
            "content": "import redis\nr = redis.Redis(host='localhost', port=6379)",
            "embedding": DenseEmbedder.embed_text("redis connection broker celery host port")
        }
    ]
    VectorStore.store_embeddings(db, submission_id, chunks)

    # 1. Razorpay track -> Compliant
    rzp_audit = SponsorComplianceAuditor.audit_track(
        db, submission_id,
        track_name="Razorpay Track",
        query="Razorpay order payment checkout paise",
        mandatory_keywords=["razorpay"],
        min_threshold=0.40
    )
    assert rzp_audit["is_compliant"] is True
    assert len(rzp_audit["evidence"]) >= 1

    # 2. Gemini track -> Non-compliant (absent)
    gem_audit = SponsorComplianceAuditor.audit_track(
        db, submission_id,
        track_name="Gemini Track",
        query="Google Gemini multimodal live streaming API",
        mandatory_keywords=["gemini"],
        min_threshold=0.60
    )
    assert gem_audit["is_compliant"] is False

    # 3. Partial keyword match -> Non-compliant because all mandatory keywords are required
    partial_audit = SponsorComplianceAuditor.audit_track(
        db, submission_id,
        track_name="Razorpay Strict Track",
        query="Razorpay order payment checkout",
        mandatory_keywords=["razorpay", "nonexistent_required_kw"],
        min_threshold=0.40
    )
    assert partial_audit["is_compliant"] is False

    db.close()

def test_judge_copilot_chat_api(client, seed_rag_submission):
    """Verifies POST /v1/evaluations/{id}/chat returns grounded answers with line citations."""
    db = TestingSessionLocal()
    sub_id = seed_rag_submission["submission_id"]

    # Seed code chunk into vector store
    chunks = [{
        "file_path": "auth/security.py",
        "symbol_name": "authenticate_bearer_token",
        "symbol_type": "function",
        "start_line": 15,
        "end_line": 35,
        "content": "def authenticate_bearer_token(header):\n    token = header.split(' ')[1]\n    return verify_hash(token)",
        "embedding": DenseEmbedder.embed_text("authenticate bearer token header hash verification security")
    }]
    VectorStore.store_embeddings(db, sub_id, chunks)
    db.close()

    headers = {"Authorization": f"Bearer {seed_rag_submission['api_key']}"}
    resp = client.post(
        f"/v1/evaluations/{sub_id}/chat",
        json={"question": "How is authentication handled in this project?"},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == sub_id
    assert "auth/security.py" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["file_path"] == "auth/security.py"
    assert data["citations"][0]["lines"] == "15-35"

def test_compliance_api_endpoint(client, seed_rag_submission):
    """Verifies GET /v1/evaluations/{id}/compliance endpoint returns structured audit."""
    sub_id = seed_rag_submission["submission_id"]
    headers = {"Authorization": f"Bearer {seed_rag_submission['api_key']}"}

    resp = client.get(
        f"/v1/evaluations/{sub_id}/compliance",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == sub_id
    assert "total_tracks_evaluated" in data
    assert "reports" in data
