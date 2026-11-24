from fastapi.testclient import TestClient

from app.core.cache import TTLCache
from app.models.common import BilingualText
from app.models.hotel import HotelDoc
from app.services.hotel_service import HotelService, compute_hotel_match_score


class FakeHotelRepo:
    def __init__(self, docs: list[HotelDoc]) -> None:
        self._docs = docs

    def list_all(self) -> list[HotelDoc]:
        return list(self._docs)

    def get_by_id(self, hotel_id: str) -> HotelDoc | None:
        for d in self._docs:
            if d.hotel_id == hotel_id or d.id == hotel_id:
                return d
        return None


def _sample_hotels() -> list[HotelDoc]:
    return [
        HotelDoc(
            hotel_id="EXAMPLE_hotel_A",
            name=BilingualText(bn="EXAMPLE সি ভিউ", en="EXAMPLE_Sea_View"),
            area="kolatoli",
            price_min_bdt=2500,
            price_max_bdt=4500,
            amenities=["wifi", "pool", "restaurant"],
            rating=4.2,
            lat=21.4167,
            lon=91.9833,
            is_verified=True,
            data_source="EXAMPLE",
            last_updated="2026-11-24T00:00:00Z",
        ),
        HotelDoc(
            hotel_id="EXAMPLE_hotel_B",
            name=BilingualText(bn="EXAMPLE বিচ ইন", en="EXAMPLE_Beach_Inn"),
            area="kolatoli",
            price_min_bdt=1800,
            price_max_bdt=3000,
            amenities=["wifi"],
            rating=3.8,
            lat=21.4180,
            lon=91.9810,
            is_verified=True,
            data_source="EXAMPLE",
            last_updated="2026-11-24T00:00:00Z",
        ),
        HotelDoc(
            hotel_id="EXAMPLE_hotel_C",
            name=BilingualText(bn="EXAMPLE গ্র্যান্ড রিসোর্ট", en="EXAMPLE_Grand_Resort"),
            area="sugandha",
            price_min_bdt=2800,
            price_max_bdt=5000,
            amenities=["wifi", "pool", "gym"],
            rating=4.5,
            lat=21.4250,
            lon=91.9750,
            is_verified=False,
            data_source="EXAMPLE",
            last_updated="2026-11-24T00:00:00Z",
        ),
    ]


def test_recommender_scoring_formula_and_tiebreak() -> None:
    """Verifies ai-spec.md §8 worked example:
    Hotel A (0.918) > Hotel B (0.707, verified) > Hotel C (0.710, unverified tie-break).
    """
    hotels = _sample_hotels()
    score_a = compute_hotel_match_score(
        hotels[0], area="kolatoli", max_price_bdt=3000, requested_amenities=["wifi", "pool"]
    )
    score_b = compute_hotel_match_score(
        hotels[1], area="kolatoli", max_price_bdt=3000, requested_amenities=["wifi", "pool"]
    )
    score_c = compute_hotel_match_score(
        hotels[2], area="kolatoli", max_price_bdt=3000, requested_amenities=["wifi", "pool"]
    )

    assert score_a == 0.918
    assert score_b == 0.707
    assert score_c == 0.710

    service = HotelService(repository=FakeHotelRepo(hotels), cache=TTLCache())  # type: ignore[arg-type]
    res = service.search_hotels(
        area="kolatoli",
        max_price_bdt=3000,
        amenities=["wifi", "pool"],
        lang="en",
        strict_filter=False,
    )
    ordered_ids = [item.hotel_id for item in res.items]
    assert ordered_ids == ["EXAMPLE_hotel_A", "EXAMPLE_hotel_B", "EXAMPLE_hotel_C"]


def test_hotels_api_filtering_and_detail(client: TestClient) -> None:
    from app.api.v1.hotels import get_hotel_service

    fake_service = HotelService(repository=FakeHotelRepo(_sample_hotels()), cache=TTLCache())  # type: ignore[arg-type]
    client.app.dependency_overrides[get_hotel_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        res = client.get(
            "/api/v1/hotels?area=kolatoli&max_price_bdt=3000&amenities=wifi,pool&lang=en"
        )
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        assert body["items"][0]["hotel_id"] == "EXAMPLE_hotel_A"
        assert body["items"][0]["match_score"] > 0.85

        detail = client.get("/api/v1/hotels/EXAMPLE_hotel_A?lang=bn")
        assert detail.status_code == 200
        assert detail.json()["name"] == "EXAMPLE সি ভিউ"

        missing = client.get("/api/v1/hotels/NON_EXISTENT")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "HOTEL_NOT_FOUND"
    finally:
        client.app.dependency_overrides.pop(get_hotel_service, None)  # type: ignore[attr-defined]
