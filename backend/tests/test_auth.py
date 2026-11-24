import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from scripts.dev_token import create_anonymous_user_token  # noqa: E402
from scripts.make_admin import promote_to_admin  # noqa: E402

from app.core.firebase import check_firestore_connection, get_firestore_client  # noqa: E402
from app.services.auth_service import map_auth_provider  # noqa: E402


def _is_auth_emulator_running() -> bool:
    host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    try:
        with urllib.request.urlopen(f"http://{host}/", timeout=1.0):
            return True
    except urllib.error.HTTPError:
        # Any HTTP response (e.g. 200/404) means the Auth emulator server is reachable
        return True
    except Exception:
        return False


def _require_emulators() -> str:
    if not check_firestore_connection(timeout_seconds=1.0):
        pytest.skip("Firestore emulator is not running at localhost:8080")
    if not _is_auth_emulator_running():
        pytest.skip("Firebase Auth emulator is not running at localhost:9099")
    return os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")


# ---------------------------------------------------------------------------
# Unit tests (no emulator required)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw_provider", "expected"),
    [
        ("anonymous", "anonymous"),
        ("google.com", "google"),
        ("password", "email"),
        ("phone", "email"),
        ("facebook.com", "email"),
        ("", "email"),
        (None, "email"),
    ],
)
def test_map_auth_provider(raw_provider: str | None, expected: str) -> None:
    """Provider claim mapping works without emulators."""
    assert map_auth_provider(raw_provider) == expected


# ---------------------------------------------------------------------------
# Integration tests (require Firestore + Auth emulators)
# ---------------------------------------------------------------------------


def test_garbage_token_returns_401_bilingual(client: TestClient) -> None:
    _require_emulators()
    garbage = "not-a-valid-firebase-jwt-token"
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {garbage}"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert body["error"]["message_bn"]
    assert body["error"]["message_en"]
    assert garbage not in response.text


def test_missing_authorization_header_returns_401(client: TestClient) -> None:
    _require_emulators()
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert body["error"]["message_bn"]
    assert body["error"]["message_en"]


def test_full_auth_profile_and_admin_lifecycle(client: TestClient) -> None:
    auth_host = _require_emulators()
    uid, token = create_anonymous_user_token(auth_host)
    headers = {"Authorization": f"Bearer {token}"}
    db = get_firestore_client()

    # 1. First register -> 201 and users/{uid} exists (tourist, anonymous)
    reg_res = client.post("/api/v1/auth/register", headers=headers, json={})
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["uid"] == uid
    assert reg_data["role"] == "tourist"
    assert reg_data["auth_provider"] == "anonymous"
    assert reg_data["preferred_language"] == "bn"
    created_at_first = reg_data["created_at"]

    doc_snap = db.collection("users").document(uid).get()
    assert doc_snap.exists
    doc_dict = doc_snap.to_dict()
    assert doc_dict["role"] == "tourist"
    assert doc_dict["auth_provider"] == "anonymous"
    assert "email" not in doc_dict
    assert "phone" not in doc_dict

    # 2. Second register -> 200 and created_at unchanged
    reg_again = client.post("/api/v1/auth/register", headers=headers, json={})
    assert reg_again.status_code == 200
    assert reg_again.json()["created_at"] == created_at_first

    # 3. GET /api/v1/me -> 200
    me_res = client.get("/api/v1/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["uid"] == uid
    assert me_res.json()["role"] == "tourist"

    # 4. PATCH /api/v1/me changes preferred_language and trims display_name
    patch_res = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"preferred_language": "en", "display_name": "  Cox Tourist  "},
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["preferred_language"] == "en"
    assert patch_data["display_name"] == "Cox Tourist"

    # 5. Body with {"role": "admin"} -> 400 INVALID_INPUT and role unchanged
    role_patch = client.patch("/api/v1/me", headers=headers, json={"role": "admin"})
    assert role_patch.status_code == 400
    assert role_patch.json()["error"]["code"] == "INVALID_INPUT"

    role_reg = client.post("/api/v1/auth/register", headers=headers, json={"role": "admin"})
    assert role_reg.status_code == 400
    assert role_reg.json()["error"]["code"] == "INVALID_INPUT"

    assert db.collection("users").document(uid).get().to_dict()["role"] == "tourist"

    # 6. display_name longer than 50 characters -> 400 INVALID_INPUT
    long_name_res = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"display_name": "A" * 51},
    )
    assert long_name_res.status_code == 400
    assert long_name_res.json()["error"]["code"] == "INVALID_INPUT"

    # 7. Tourist token on /api/v1/admin/ping -> 403 FORBIDDEN
    ping_forbidden = client.get("/api/v1/admin/ping", headers=headers)
    assert ping_forbidden.status_code == 403
    assert ping_forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert ping_forbidden.json()["error"]["message_bn"]
    assert ping_forbidden.json()["error"]["message_en"]

    # 8. After make_admin logic promotes user, same user gets 200 on /api/v1/admin/ping
    promote_to_admin(uid)
    ping_ok = client.get("/api/v1/admin/ping", headers=headers)
    assert ping_ok.status_code == 200
    assert ping_ok.json() == {"ok": True}

    # 9. Seed usage/{uid_date} doc, DELETE /api/v1/me -> 204, usage deleted, GET /me -> 404
    usage_doc_id = f"{uid}_2026-11-24"
    db.collection("usage").document(usage_doc_id).set(
        {
            "uid": uid,
            "date": "2026-11-24",
            "chat_count": 3,
            "last_chat_at": datetime.now(UTC),
        }
    )

    delete_res = client.delete("/api/v1/me", headers=headers)
    assert delete_res.status_code == 204
    assert not db.collection("users").document(uid).get().exists
    assert not db.collection("usage").document(usage_doc_id).get().exists

    after_delete = client.get("/api/v1/me", headers=headers)
    assert after_delete.status_code == 404
    assert after_delete.json()["error"]["code"] == "USER_NOT_FOUND"
    assert after_delete.json()["error"]["message_bn"]
    assert after_delete.json()["error"]["message_en"]
