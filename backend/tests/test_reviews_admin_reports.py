from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.v1.admin import get_admin_service as get_admin_router_service
from app.api.v1.reports import get_admin_service as get_reports_router_service
from app.api.v1.reviews import get_review_service
from app.core.auth import require_admin, require_auth
from app.core.cache import TTLCache
from app.models.admin import ReportCreateRequest, ReportDoc
from app.models.common import BilingualText
from app.models.review import ReviewDoc, SentimentResult
from app.models.safety import BeachStatusDoc, BeachZoneId, FlagColour
from app.models.user import UserContext
from app.services.admin_service import AdminService
from app.services.review_service import ReviewService, analyze_review_sentiment


class FakeReviewRepo:
    def __init__(self) -> None:
        self.reviews: list[ReviewDoc] = []

    def create(
        self,
        hotel_id: str,
        uid: str,
        rating: int,
        comment: str,
        sentiment: SentimentResult,
    ) -> ReviewDoc:
        doc = ReviewDoc(
            review_id="EXAMPLE_rev_001",
            hotel_id=hotel_id,
            uid=uid,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC),
            sentiment=sentiment,
        )
        self.reviews.append(doc)
        return doc

    def list_by_hotel(self, hotel_id: str) -> list[ReviewDoc]:
        return [r for r in self.reviews if r.hotel_id == hotel_id]


class FakeSafetyRepoForAdmin:
    def update_beach_flag(
        self,
        zone_id: BeachZoneId,
        flag_colour: FlagColour,
        note_bn: str,
        note_en: str,
        set_by: str,
    ) -> BeachStatusDoc:
        return BeachStatusDoc(
            zone_id=zone_id,
            zone_name=BilingualText(bn="কলাতলী", en="Kolatoli"),
            flag_colour=flag_colour,
            note=BilingualText(bn=note_bn, en=note_en),
            set_by=set_by,
            last_updated="2026-11-24T16:00:00Z",
        )


class FakeReportRepo:
    def __init__(self) -> None:
        self.reports: list[ReportDoc] = []

    def create(
        self,
        payload: ReportCreateRequest,
        uid: str | None = None,
    ) -> ReportDoc:
        doc = ReportDoc(
            report_id="EXAMPLE_rep_555",
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            issue_description=payload.issue_description,
            reported_by_uid=uid,
            status="pending",
            created_at=datetime.now(UTC),
        )
        self.reports.append(doc)
        return doc

    def list_all(self, status_filter: str | None = None) -> list[ReportDoc]:
        return list(self.reports)


def test_lexicon_sentiment_analysis_en_and_bn_with_negation() -> None:
    pos_en = analyze_review_sentiment("Room was clean and great", "en")
    assert pos_en.overall == "positive"
    assert pos_en.aspects["Cleanliness"].sentiment == "positive"

    neg_bn = analyze_review_sentiment("ঘর নোংরা এবং গন্ধ", "bn")
    assert neg_bn.overall == "negative"
    assert neg_bn.aspects["Cleanliness"].sentiment == "negative"

    negated_en = analyze_review_sentiment("The room was not clean", "en")
    assert negated_en.overall == "negative"

    negated_bn = analyze_review_sentiment("ঘর পরিষ্কার না", "bn")
    assert negated_bn.overall == "negative"


def test_reviews_admin_flag_update_and_report_submission(client: TestClient) -> None:
    fake_rev_service = ReviewService(repository=FakeReviewRepo())  # type: ignore[arg-type]
    cache: TTLCache[object] = TTLCache()
    cache.set("hotels:all", ["cached_entry"])
    fake_admin_service = AdminService(
        safety_repository=FakeSafetyRepoForAdmin(),  # type: ignore[arg-type]
        report_repository=FakeReportRepo(),  # type: ignore[arg-type]
        cache=cache,
    )

    client.app.dependency_overrides[get_review_service] = lambda: fake_rev_service  # type: ignore[attr-defined]
    client.app.dependency_overrides[get_admin_router_service] = lambda: fake_admin_service  # type: ignore[attr-defined]
    client.app.dependency_overrides[get_reports_router_service] = lambda: fake_admin_service  # type: ignore[attr-defined]
    client.app.dependency_overrides[require_auth] = lambda: UserContext(  # type: ignore[attr-defined]
        uid="EXAMPLE_tourist_1", role="tourist"
    )
    client.app.dependency_overrides[require_admin] = lambda: UserContext(  # type: ignore[attr-defined]
        uid="EXAMPLE_admin_1", role="admin"
    )

    try:
        # 1. Submit hotel review -> 201 with sentiment breakdown
        rev_res = client.post(
            "/api/v1/hotels/EXAMPLE_hotel_001/reviews",
            json={"rating": 5, "comment": "Room was clean and staff was friendly", "lang": "en"},
        )
        assert rev_res.status_code == 201
        assert rev_res.json()["sentiment"]["overall"] == "positive"

        # 2. Admin PUT /api/v1/admin/beach-status/kolatoli -> 200 and clears cache
        flag_res = client.put(
            "/api/v1/admin/beach-status/kolatoli",
            json={"flag": "red"},
        )
        assert flag_res.status_code == 200
        assert flag_res.json()["flag"] == "red"
        assert cache.get("hotels:all") is None

        # 3. Report wrong info -> 201 bilingual confirmation
        rep_res = client.post(
            "/api/v1/reports",
            json={
                "entity_type": "hotel",
                "entity_id": "EXAMPLE_hotel_001",
                "issue_description": "Swimming pool is closed for maintenance.",
            },
        )
        assert rep_res.status_code == 201
        assert rep_res.json()["report_id"] == "EXAMPLE_rep_555"
        assert rep_res.json()["message_bn"]
        assert rep_res.json()["message_en"]
    finally:
        client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
