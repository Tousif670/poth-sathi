from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.place import PlaceDoc

PLACES_COLLECTION = "places"


class PlaceRepository:
    """Firestore repository for places/{place_id} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def list_all(self) -> list[PlaceDoc]:
        try:
            docs = list(self.db.collection(PLACES_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[PlaceDoc] = []
        for snap in docs:
            data = snap.to_dict() or {}
            data.setdefault("id", snap.id)
            data.setdefault("place_id", snap.id)
            results.append(PlaceDoc.model_validate(data))
        return results
