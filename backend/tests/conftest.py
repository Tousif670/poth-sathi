import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Ensure APP_ENV is test for test runs
os.environ["APP_ENV"] = "test"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"

from app.core.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing test environment settings."""
    get_settings.cache_clear()
    settings = Settings(
        APP_ENV="test",
        FIREBASE_PROJECT_ID="demo-pothsathi",
        FIRESTORE_EMULATOR_HOST="localhost:8080",
        FIREBASE_AUTH_EMULATOR_HOST="localhost:9099",
    )
    return settings


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Test client fixture for FastAPI app."""
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
