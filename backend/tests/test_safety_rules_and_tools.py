from fastapi.testclient import TestClient

from app.agents.tool_executor import ToolExecutor
from app.api.v1.chat import get_chat_service
from app.core.cache import TTLCache
from app.core.llm_client import FakeLLMClient, LLMToolCall
from app.core.rate_limiter import RateLimiter
from app.models.common import BilingualText
from app.models.hotel import HotelDoc
from app.services.chat_service import ChatService
from app.services.hotel_service import HotelService


class FakeHotelRepo:
    def list_all(self) -> list[HotelDoc]:
        return [
            HotelDoc(
                hotel_id="EXAMPLE_hotel_001",
                name=BilingualText(bn="EXAMPLE হোটেল ০১", en="EXAMPLE Hotel 001"),
                area="kolatoli",
                price_min_bdt=2000,
                price_max_bdt=4500,
                amenities=["wifi", "pool"],
                rating=4.2,
                lat=21.4172,
                lon=91.9810,
                is_verified=True,
                data_source="EXAMPLE",
                last_updated="2026-11-24T00:00:00Z",
            )
        ]


def test_emergency_queries_intercepted_before_llm_in_bn_en_banglish(
    client: TestClient,
) -> None:
    fake_llm = FakeLLMClient()
    fake_service = ChatService(
        llm_client=fake_llm,
        rate_limiter=RateLimiter(),
    )
    client.app.dependency_overrides[get_chat_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        prompts = [
            ("I am drowning near Kolatoli", "en"),
            ("কলাতলীতে মানুষ ডুবে যাচ্ছে!", "bn"),
            ("ami dube jacchi help", "en"),
            ("মানিব্যাগ হারিয়ে গেছে, কী করব?", "bn"),
        ]
        for text, lang in prompts:
            res = client.post(
                "/api/v1/chat/messages",
                json={"message": text, "language": lang},
            )
            assert res.status_code == 200
            body = res.json()
            assert body["safety_triggered"] is True
            assert "999" in body["answer_text"] or "৯৯৯" in body["answer_text"]
            assert len(body["cards"]) == 1

        # Zero LLM calls were made for all emergency prompts
        assert len(fake_llm.calls) == 0
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]


def test_gemini_function_calling_dispatches_search_hotels_tool(
    client: TestClient,
) -> None:
    fake_llm = FakeLLMClient(
        canned_text="Here are verified hotels in Kolatoli under ৳3000 with WiFi.",
        canned_tool_calls=[
            LLMToolCall(
                name="search_hotels",
                args={"area": "kolatoli", "max_price_bdt": 3000, "amenities": ["wifi"]},
            )
        ],
    )
    fake_hotel_service = HotelService(
        repository=FakeHotelRepo(),  # type: ignore[arg-type]
        cache=TTLCache(),
    )
    executor = ToolExecutor(hotel_service=fake_hotel_service)
    fake_service = ChatService(
        llm_client=fake_llm,
        rate_limiter=RateLimiter(),
        tool_executor=executor,
    )
    client.app.dependency_overrides[get_chat_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        res = client.post(
            "/api/v1/chat/messages",
            json={"message": "hotels in Kolatoli under 3000 with wifi", "language": "en"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["safety_triggered"] is False
        assert body["tool_calls_used"] == ["search_hotels"]
        assert len(body["cards"]) == 1
        assert body["cards"][0]["type"] == "hotel"
        assert body["cards"][0]["data"]["hotel_id"] == "EXAMPLE_hotel_001"
        assert body["sources"][0]["source_id"] == "hotels/EXAMPLE_hotel_001"
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]
