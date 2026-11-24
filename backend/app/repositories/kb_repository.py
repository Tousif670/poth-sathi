from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.kb import KBChunkDoc

KB_CHUNKS_COLLECTION = "kb_chunks"


class KBRepository:
    """Firestore repository for kb_chunks/{chunk_id} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def list_all(self) -> list[KBChunkDoc]:
        try:
            docs = list(self.db.collection(KB_CHUNKS_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[KBChunkDoc] = []
        for snap in docs:
            data = snap.to_dict() or {}
            data.setdefault("id", snap.id)
            data.setdefault("chunk_id", snap.id)
            results.append(KBChunkDoc.model_validate(data))
        return results
