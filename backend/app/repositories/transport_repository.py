from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.transport import RouteDoc

TRANSPORT_ROUTES_COLLECTION = "transport_routes"


class TransportRepository:
    """Firestore repository for transport_routes/{route_id} documents (D22)."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def list_all(self) -> list[RouteDoc]:
        try:
            docs = list(self.db.collection(TRANSPORT_ROUTES_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[RouteDoc] = []
        for snap in docs:
            data = snap.to_dict() or {}
            data.setdefault("id", snap.id)
            data.setdefault("route_id", snap.id)
            results.append(RouteDoc.model_validate(data))
        return results
