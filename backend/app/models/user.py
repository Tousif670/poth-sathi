from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

UserRole = Literal["tourist", "admin"]
AuthProvider = Literal["anonymous", "google", "email"]
PreferredLanguage = Literal["bn", "en"]

MAX_DISPLAY_NAME_LENGTH = 50


def _validate_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if len(trimmed) > MAX_DISPLAY_NAME_LENGTH:
        raise ValueError(f"display_name must be at most {MAX_DISPLAY_NAME_LENGTH} characters")
    if not trimmed:
        return None
    return trimmed


class UserDoc(BaseModel):
    """Firestore document schema for users/{uid} (docs/firestore-schema.md §3.1)."""

    model_config = ConfigDict(extra="ignore")

    uid: str
    role: UserRole = "tourist"
    display_name: str | None = None
    auth_provider: AuthProvider
    preferred_language: PreferredLanguage = "bn"
    created_at: datetime
    last_login: datetime


class UserProfile(BaseModel):
    """API response schema for user profile endpoints (docs/api-spec.md §2)."""

    uid: str
    role: UserRole
    display_name: str | None = None
    auth_provider: AuthProvider
    preferred_language: PreferredLanguage
    created_at: datetime
    last_login: datetime


class RegisterRequest(BaseModel):
    """Request body for POST /api/v1/auth/register."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    preferred_language: PreferredLanguage | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str | None) -> str | None:
        return _validate_display_name(v)


class UpdateProfileRequest(BaseModel):
    """Request body for PATCH /api/v1/me."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    preferred_language: PreferredLanguage | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str | None) -> str | None:
        return _validate_display_name(v)


class UserContext(BaseModel):
    """Authenticated user identity and role attached by auth dependencies."""

    uid: str
    role: UserRole = "tourist"
