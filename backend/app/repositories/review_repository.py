import uuid
from datetime import UTC, datetime

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.review import ReviewDoc, SentimentResult

HOTELS_COLLECTION = "hotels"
REVIEWS_SUBCOLLECTION = "reviews"


class ReviewRepository:
    """Firestore repository for hotels/{hotel_id}/reviews/{review_id} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def create(
        self,
        hotel_id: str,
        uid: str,
        rating: int,
        comment: str,
        sentiment: SentimentResult,
    ) -> ReviewDoc:
        rev_id = f"rev_{uuid.uuid4().hex[:10]}"
        doc = ReviewDoc(
            review_id=rev_id,
            hotel_id=hotel_id,
            uid=uid,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC),
            sentiment=sentiment,
        )
        try:
            (
                self.db.collection(HOTELS_COLLECTION)
                .document(hotel_id)
                .collection(REVIEWS_SUBCOLLECTION)
                .document(rev_id)
                .set(doc.model_dump())
            )
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return doc

    def list_by_hotel(self, hotel_id: str) -> list[ReviewDoc]:
        try:
            snaps = list(
                self.db.collection(HOTELS_COLLECTION)
                .document(hotel_id)
                .collection(REVIEWS_SUBCOLLECTION)
                .stream()
            )
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[ReviewDoc] = []
        for snap in snaps:
            data = snap.to_dict() or {}
            data.setdefault("review_id", snap.id)
            data.setdefault("hotel_id", hotel_id)
            results.append(ReviewDoc.model_validate(data))
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results
