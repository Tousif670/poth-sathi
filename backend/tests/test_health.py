from fastapi.testclient import TestClient


def test_health_endpoint_structure(client: TestClient):
    """GET /api/v1/health returns status, app_env, and firestore status without secrets."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "ok"
    assert "app_env" in data
    assert data["app_env"] == "test"
    assert "firestore" in data
    assert data["firestore"] in ("ok", "down")

    # Verify no secrets or credentials leaked
    assert "key" not in data
    assert "secret" not in data
    assert "password" not in data
    assert "token" not in data
