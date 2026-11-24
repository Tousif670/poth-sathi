from fastapi.testclient import TestClient

from app.api.v1.chat import get_chat_service
from app.core.auth import get_optional_user
from app.core.llm_client import FakeLLMClient
from app.core.rate_limiter import RateLimiter
from app.models.user import UserContext
from app.services.chat_service import ChatService, strip_pii


def test_strip_pii_removes_emails_and_phones() -> None:
    raw = "My email is tourist@example.com and phone is +8801712345678, help me find a hotel."
    cleaned = strip_pii(raw)
    assert "tourist@example.com" not in cleaned
    assert "01712345678" not in cleaned
    assert "[REDACTED_EMAIL]" in cleaned
    assert "[REDACTED_PHONE]" in cleaned


def test_input_too_long_returns_400_bilingual(client: TestClient) -> None:
    fake_service = ChatService(
        llm_client=FakeLLMClient(),
        rate_limiter=RateLimiter(user_daily_limit=50),
    )
    client.app.dependency_overrides[get_chat_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        res = client.post("/api/v1/chat/messages", json={"message": "A" * 2001})
        assert res.status_code == 400
        body = res.json()
        assert body["error"]["code"] == "INPUT_TOO_LONG"
        assert body["error"]["message_bn"]
        assert body["error"]["message_en"]
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]


def test_user_rate_limit_51st_call_returns_429_and_global_ai_rest(client: TestClient) -> None:
    fake_llm = FakeLLMClient(canned_text="কলাতলী সৈকতে স্বাগতম।")
    limiter = RateLimiter(user_daily_limit=50, ip_hourly_limit=500, global_daily_ai_limit=100)
    fake_service = ChatService(llm_client=fake_llm, rate_limiter=limiter)

    client.app.dependency_overrides[get_chat_service] = lambda: fake_service  # type: ignore[attr-defined]
    client.app.dependency_overrides[get_optional_user] = lambda: UserContext(  # type: ignore[attr-defined]
        uid="EXAMPLE_UID_rate", role="tourist"
    )

    try:
        # Calls 1..50 succeed
        for i in range(50):
            res = client.post(
                "/api/v1/chat/messages",
                json={"message": f"কলাতলী হোটেল তথ্য {i} email test@example.com"},
            )
            assert res.status_code == 200
            assert res.headers["X-RateLimit-Limit"] == "50"
            assert res.headers["X-RateLimit-Remaining"] == str(50 - (i + 1))

        # Verify PII was stripped before reaching FakeLLMClient
        last_sent = fake_llm.calls[-1]["messages"][0]["content"]
        assert "test@example.com" not in last_sent

        # 51st call raises HTTP 429 RATE_LIMITED
        over_res = client.post("/api/v1/chat/messages", json={"message": "আরেকটি প্রশ্ন"})
        assert over_res.status_code == 429
        assert over_res.json()["error"]["code"] == "RATE_LIMITED"
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]
        client.app.dependency_overrides.pop(get_optional_user, None)  # type: ignore[attr-defined]


def test_global_daily_ai_cap_triggers_ai_resting_mode(client: TestClient) -> None:
    limiter = RateLimiter(user_daily_limit=50, ip_hourly_limit=500, global_daily_ai_limit=1)
    fake_service = ChatService(llm_client=FakeLLMClient(), rate_limiter=limiter)
    client.app.dependency_overrides[get_chat_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        first = client.post("/api/v1/chat/messages", json={"message": "Hello Cox's Bazar"})
        assert first.status_code == 200
        assert first.json()["is_ai_resting"] is False

        second = client.post("/api/v1/chat/messages", json={"message": "আজ সমুদ্র কেমন?"})
        assert second.status_code == 200
        body = second.json()
        assert body["is_ai_resting"] is True
        assert body["fallback_used"] is True
        assert "বিশ্রামে" in body["answer_text"]
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]
