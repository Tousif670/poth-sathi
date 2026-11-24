from fastapi.testclient import TestClient

from app.agents.tool_executor import ToolExecutor
from app.api.v1.chat import get_chat_service
from app.core.cache import TTLCache
from app.core.llm_client import FakeLLMClient, LLMQuotaError
from app.core.rate_limiter import RateLimiter
from app.models.common import BilingualText
from app.models.hotel import HotelDoc
from app.models.kb import KBChunkDoc
from app.services.chat_service import ChatService
from app.services.hotel_service import HotelService
from app.services.rag_service import RAGService


class FakeHotelRepo:
    def list_all(self) -> list[HotelDoc]:
        return [
            HotelDoc(
                hotel_id="EXAMPLE_hotel_001",
                name=BilingualText(bn="EXAMPLE হোটেল ০১", en="EXAMPLE Hotel 001"),
                area="kolatoli",
                price_min_bdt=2000,
                price_max_bdt=4500,
                amenities=["wifi"],
                rating=4.2,
                lat=21.4172,
                lon=91.9810,
                is_verified=False,
                data_source="EXAMPLE",
                last_updated="2026-11-24T00:00:00Z",
            )
        ]


def _sample_chunks() -> list[KBChunkDoc]:
    return [
        KBChunkDoc(
            chunk_id="EXAMPLE_kb_rip",
            category="beach_safety",
            text=BilingualText(
                bn="রিপ কারেন্টে পড়লে সৈকতের সমান্তরালে সাঁতার কাটুন।",
                en="If caught in a rip current, swim parallel to the shoreline.",
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
        KBChunkDoc(
            chunk_id="EXAMPLE_kb_food",
            category="food_guide",
            text=BilingualText(
                bn="কক্সবাজারে সামুদ্রিক মাছ ও শুঁটকি জনপ্রিয়।",
                en="Seafood and dried fish are popular in Cox's Bazar.",
            ),
            embedding=[0.0, 1.0, 0.0],
        ),
    ]


def test_rag_vector_and_keyword_search_returns_top_chunks() -> None:
    rag = RAGService(initial_chunks=_sample_chunks())

    # 1. Vector cosine similarity search
    vec_hits = rag.search("rip", lang="en", query_embedding=[0.95, 0.05, 0.0], top_k=3)
    assert len(vec_hits) == 1
    assert vec_hits[0].chunk_id == "EXAMPLE_kb_rip"
    assert vec_hits[0].relevance_score >= 0.9

    # 2. Keyword fallback search when query_embedding is omitted
    kw_hits = rag.search("seafood popular Cox's Bazar", lang="en", top_k=3)
    assert len(kw_hits) >= 1
    assert kw_hits[0].chunk_id == "EXAMPLE_kb_food"


def test_gemini_429_quota_exhaustion_routes_to_keyword_rag_fallback_and_ai_resting(
    client: TestClient,
) -> None:
    rag = RAGService(initial_chunks=_sample_chunks())
    fake_hotel_service = HotelService(
        repository=FakeHotelRepo(),  # type: ignore[arg-type]
        cache=TTLCache(),
    )
    executor = ToolExecutor(hotel_service=fake_hotel_service, rag_service=rag)
    failing_llm = FakeLLMClient(raise_error=LLMQuotaError("429 quota exceeded"))

    fake_chat_service = ChatService(
        llm_client=failing_llm,
        rate_limiter=RateLimiter(),
        tool_executor=executor,
        rag_service=rag,
    )
    client.app.dependency_overrides[get_chat_service] = lambda: fake_chat_service  # type: ignore[attr-defined]

    try:
        # 1. Hotel intent query triggers keyword router -> hotel card + rest message
        res_hotel = client.post(
            "/api/v1/chat/messages",
            json={"message": "কলাতলী হোটেল দেখান", "language": "bn"},
        )
        assert res_hotel.status_code == 200
        body_hotel = res_hotel.json()
        assert body_hotel["fallback_used"] is True
        assert body_hotel["is_ai_resting"] is True
        assert "বিশ্রামে" in body_hotel["answer_text"]
        assert len(body_hotel["cards"]) == 1
        assert body_hotel["cards"][0]["type"] == "hotel"

        # 2. Knowledge query triggers RAG chunk fallback + sources
        res_kb = client.post(
            "/api/v1/chat/messages",
            json={"message": "What seafood is popular?", "language": "en"},
        )
        assert res_kb.status_code == 200
        body_kb = res_kb.json()
        assert body_kb["fallback_used"] is True
        assert body_kb["is_ai_resting"] is True
        assert "Seafood" in body_kb["answer_text"]
        assert body_kb["sources"][0]["source_id"] == "kb_chunks/EXAMPLE_kb_food"
    finally:
        client.app.dependency_overrides.pop(get_chat_service, None)  # type: ignore[attr-defined]
