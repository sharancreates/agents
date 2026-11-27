import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.models import Base
from api.auth import get_db, _RATE_LIMIT_WINDOWS

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes tables before each test and cleans them after."""
    Base.metadata.create_all(bind=test_engine)
    _RATE_LIMIT_WINDOWS.clear()
    yield
    Base.metadata.drop_all(bind=test_engine)
    _RATE_LIMIT_WINDOWS.clear()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_client():
    return TestClient(app)
