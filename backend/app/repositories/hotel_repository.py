from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.hotel import HotelDoc

HOTELS_COLLECTION = "hotels"


class HotelRepository:
    """Firestore repository for hotels/{hotel_id} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def list_all(self) -> list[HotelDoc]:
        try:
            docs = list(self.db.collection(HOTELS_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[HotelDoc] = []
        for snap in docs:
            data = snap.to_dict() or {}
            data.setdefault("id", snap.id)
            data.setdefault("hotel_id", snap.id)
            results.append(HotelDoc.model_validate(data))
        return results

    def get_by_id(self, hotel_id: str) -> HotelDoc | None:
        try:
            snap = self.db.collection(HOTELS_COLLECTION).document(hotel_id).get()
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        if not snap.exists:
            return None

        data = snap.to_dict() or {}
        data.setdefault("id", snap.id)
        data.setdefault("hotel_id", snap.id)
        return HotelDoc.model_validate(data)
