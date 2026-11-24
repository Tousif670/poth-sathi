import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.chat import ChatLanguage, ChatMessageDoc, ChatSessionDoc

CHAT_SESSIONS_COLLECTION = "chat_sessions"
MESSAGES_SUBCOLLECTION = "messages"
RETENTION_DAYS = 30  # D14: Chat history kept 30 days at most


class ChatRepository:
    """Firestore repository for chat_sessions/{session_id} and messages subcollection."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def ensure_session(
        self,
        uid: str,
        session_id: str | None = None,
        language: ChatLanguage = "bn",
    ) -> ChatSessionDoc:
        now = datetime.now(UTC)
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        doc_ref = self.db.collection(CHAT_SESSIONS_COLLECTION).document(sid)

        try:
            snap = doc_ref.get()
            if snap.exists:
                data = snap.to_dict() or {}
                data["updated_at"] = now
                doc_ref.update({"updated_at": now})
                data.setdefault("session_id", sid)
                return ChatSessionDoc.model_validate(data)

            session_doc = ChatSessionDoc(
                session_id=sid,
                uid=uid,
                language=language,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=RETENTION_DAYS),
            )
            doc_ref.set(session_doc.model_dump())
            return session_doc
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

    def save_message(
        self,
        session_id: str,
        role: Literal["user", "assistant"],
        content: str,
        language: ChatLanguage = "bn",
    ) -> ChatMessageDoc:
        now = datetime.now(UTC)
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        msg = ChatMessageDoc(
            message_id=msg_id,
            role=role,
            content=content,
            language=language,
            created_at=now,
        )
        try:
            (
                self.db.collection(CHAT_SESSIONS_COLLECTION)
                .document(session_id)
                .collection(MESSAGES_SUBCOLLECTION)
                .document(msg_id)
                .set(msg.model_dump())
            )
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return msg

    def list_sessions_for_user(self, uid: str) -> list[ChatSessionDoc]:
        try:
            snaps = list(
                self.db.collection(CHAT_SESSIONS_COLLECTION)
                .where(filter=FieldFilter("uid", "==", uid))
                .stream()
            )
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[ChatSessionDoc] = []
        for snap in snaps:
            data = snap.to_dict() or {}
            data.setdefault("session_id", snap.id)
            results.append(ChatSessionDoc.model_validate(data))
        results.sort(key=lambda s: s.updated_at, reverse=True)
        return results

    def list_messages(self, session_id: str) -> list[ChatMessageDoc]:
        try:
            snaps = list(
                self.db.collection(CHAT_SESSIONS_COLLECTION)
                .document(session_id)
                .collection(MESSAGES_SUBCOLLECTION)
                .stream()
            )
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[ChatMessageDoc] = []
        for snap in snaps:
            data = snap.to_dict() or {}
            data.setdefault("message_id", snap.id)
            results.append(ChatMessageDoc.model_validate(data))
        results.sort(key=lambda m: m.created_at)
        return results

    def delete_session(self, session_id: str, uid: str) -> bool:
        doc_ref = self.db.collection(CHAT_SESSIONS_COLLECTION).document(session_id)
        try:
            snap = doc_ref.get()
            if not snap.exists:
                return False
            data = snap.to_dict() or {}
            if data.get("uid") != uid:
                return False
            for msg_snap in doc_ref.collection(MESSAGES_SUBCOLLECTION).stream():
                msg_snap.reference.delete()
            doc_ref.delete()
            return True
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
