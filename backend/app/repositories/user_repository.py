from typing import Any

from google.api_core.exceptions import GoogleAPICallError, NotFound
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.user import UserDoc, UserRole

USERS_COLLECTION = "users"
USAGE_COLLECTION = "usage"


class UserRepository:
    """Firestore repository for users/{uid} and user-scoped usage/{uid_date} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def get(self, uid: str) -> UserDoc | None:
        try:
            snapshot = self.db.collection(USERS_COLLECTION).document(uid).get()
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        if not snapshot.exists:
            return None

        data = snapshot.to_dict() or {}
        data.setdefault("uid", uid)
        return UserDoc.model_validate(data)

    def create(self, user: UserDoc) -> UserDoc:
        try:
            self.db.collection(USERS_COLLECTION).document(user.uid).set(user.model_dump())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return user

    def update_fields(self, uid: str, fields: dict[str, Any]) -> UserDoc | None:
        doc_ref = self.db.collection(USERS_COLLECTION).document(uid)
        try:
            doc_ref.update(fields)
            snapshot = doc_ref.get()
        except NotFound:
            return None
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        if not snapshot.exists:
            return None

        data = snapshot.to_dict() or {}
        data.setdefault("uid", uid)
        return UserDoc.model_validate(data)

    def delete(self, uid: str) -> bool:
        doc_ref = self.db.collection(USERS_COLLECTION).document(uid)
        try:
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return False
            doc_ref.delete()
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return True

    def get_role(self, uid: str) -> UserRole:
        try:
            snapshot = self.db.collection(USERS_COLLECTION).document(uid).get()
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        if not snapshot.exists:
            return "tourist"

        data = snapshot.to_dict() or {}
        return "admin" if data.get("role") == "admin" else "tourist"

    def delete_usage_for_user(self, uid: str) -> int:
        """Delete all usage/{uid_date} documents belonging to uid (firestore-schema.md §3.10)."""
        usage_col = self.db.collection(USAGE_COLLECTION)
        refs_by_id: dict[str, Any] = {}

        try:
            # Query by uid field (required by schema §3.10)
            for doc in usage_col.where(filter=FieldFilter("uid", "==", uid)).stream():
                refs_by_id[doc.id] = doc.reference

            # Also match by document ID prefix "{uid}_" (doc id format: {uid}_{YYYY-MM-DD})
            prefix_start = usage_col.document(f"{uid}_")
            prefix_end = usage_col.document(f"{uid}`")  # chr(ord("_") + 1) == "`"
            for doc in (
                usage_col.order_by("__name__")
                .start_at([prefix_start])
                .end_before([prefix_end])
                .stream()
            ):
                refs_by_id[doc.id] = doc.reference

            if not refs_by_id:
                return 0

            refs = list(refs_by_id.values())
            for i in range(0, len(refs), 400):
                batch = self.db.batch()
                for ref in refs[i : i + 400]:
                    batch.delete(ref)
                batch.commit()
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        return len(refs_by_id)
