import pytest
import tempfile
import os
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient

from shortener.db import get_session
from shortener.models import *  # noqa: F403
from main import app


# Create a temporary file-based SQLite database for tests
# This avoids SQLite threading issues with in-memory databases
_test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_test_db_path = _test_db_file.name
_test_db_file.close()

TEST_DATABASE_URL = f"sqlite:///{_test_db_path}"
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up and tear down test database for each test."""
    # Create tables
    SQLModel.metadata.create_all(test_engine)
    yield
    # Clean up: drop all tables
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    """Create a test client with overridden database dependency."""

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# Cleanup test database file after all tests
def pytest_sessionfinish(session, exitstatus):
    """Clean up test database file after all tests."""
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.fixture
def sample_link_data():
    """Sample link data for testing."""
    return {"original_url": "https://example.com", "short_name": "abc123", "clicks": 0}
