from datetime import UTC, datetime
from typing import Any

from app.core.errors import UserNotFoundError
from app.models.user import (
    AuthProvider,
    RegisterRequest,
    UpdateProfileRequest,
    UserDoc,
    UserProfile,
    UserRole,
)
from app.repositories.user_repository import UserRepository


def map_auth_provider(sign_in_provider: str | None) -> AuthProvider:
    """Map Firebase token claim firebase.sign_in_provider to schema auth_provider."""
    if sign_in_provider == "anonymous":
        return "anonymous"
    if sign_in_provider == "google.com":
        return "google"
    if sign_in_provider == "password":
        return "email"
    return "email"


class AuthService:
    """Business logic for user registration, profile retrieval, update, and deletion."""

    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self._repo = user_repository if user_repository is not None else UserRepository()

    def register(
        self,
        uid: str,
        sign_in_provider: str | None,
        payload: RegisterRequest,
    ) -> tuple[UserProfile, bool]:
        """Idempotent user registration.

        First call creates users/{uid} with role='tourist' and returns (profile, True).
        Repeated calls update last_login only and return (profile, False) with created_at unchanged.
        """
        now = datetime.now(UTC)
        existing = self._repo.get(uid)

        if existing is None:
            user_doc = UserDoc(
                uid=uid,
                role="tourist",
                display_name=payload.display_name,
                auth_provider=map_auth_provider(sign_in_provider),
                preferred_language=payload.preferred_language or "bn",
                created_at=now,
                last_login=now,
            )
            created_doc = self._repo.create(user_doc)
            return UserProfile.model_validate(created_doc.model_dump()), True

        updated_doc = self._repo.update_fields(uid, {"last_login": now})
        if updated_doc is None:
            raise UserNotFoundError()
        return UserProfile.model_validate(updated_doc.model_dump()), False

    def get_me(self, uid: str) -> UserProfile:
        doc = self._repo.get(uid)
        if doc is None:
            raise UserNotFoundError()
        return UserProfile.model_validate(doc.model_dump())

    def update_me(self, uid: str, payload: UpdateProfileRequest) -> UserProfile:
        existing = self._repo.get(uid)
        if existing is None:
            raise UserNotFoundError()

        fields: dict[str, Any] = {}
        if "display_name" in payload.model_fields_set:
            fields["display_name"] = payload.display_name
        if "preferred_language" in payload.model_fields_set and payload.preferred_language:
            fields["preferred_language"] = payload.preferred_language

        if not fields:
            return UserProfile.model_validate(existing.model_dump())

        updated = self._repo.update_fields(uid, fields)
        if updated is None:
            raise UserNotFoundError()
        return UserProfile.model_validate(updated.model_dump())

    def delete_me(self, uid: str) -> None:
        existing = self._repo.get(uid)
        if existing is None:
            raise UserNotFoundError()

        self._repo.delete_usage_for_user(uid)
        self._repo.delete(uid)

    def get_role(self, uid: str) -> UserRole:
        return self._repo.get_role(uid)
