import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings


def test_prod_environment_refuses_to_start_when_gemini_or_firebase_keys_missing() -> None:
    """Per D19: In prod the app fails loudly if Firestore or Gemini keys are missing."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is missing"):
        Settings(
            APP_ENV="prod",
            FIREBASE_PROJECT_ID="pothsathi-prod-123",
            GOOGLE_APPLICATION_CREDENTIALS="/etc/secrets/firebase-sa.json",
            GEMINI_API_KEY=None,
        )

    with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        Settings(
            APP_ENV="prod",
            FIREBASE_PROJECT_ID="pothsathi-prod-123",
            GOOGLE_APPLICATION_CREDENTIALS=None,
            GEMINI_API_KEY="AIzaSyFakeKey",
        )


def test_health_endpoint_includes_rag_chunks_and_quota_diagnostics(
    client: TestClient,
) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["environment"] == "test"
    assert isinstance(body["rag_chunks"], int)
    assert body["rag_chunks"] >= 1
    assert isinstance(body["ai_quota_remaining"], int)
    assert isinstance(body["uptime_sec"], int)
