import firebase_admin
from fastapi import Depends, Request
from firebase_admin import auth as firebase_auth

from app.core.errors import ForbiddenError, InvalidTokenError
from app.core.firebase import initialize_firebase
from app.models.user import UserContext
from app.repositories.user_repository import UserRepository


def _extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header.

    Returns None when the Authorization header is absent.
    Raises InvalidTokenError when the header is present but malformed.
    Never includes the token in error messages or logs.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return None

    parts = auth_header.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise InvalidTokenError()

    return parts[1].strip()


def _verify_token_to_context(request: Request, token: str) -> UserContext:
    if not firebase_admin._apps:
        initialize_firebase()

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise InvalidTokenError() from exc

    uid = decoded.get("uid")
    if not uid or not isinstance(uid, str):
        raise InvalidTokenError()

    firebase_claim = decoded.get("firebase")
    sign_in_provider = (
        firebase_claim.get("sign_in_provider") if isinstance(firebase_claim, dict) else None
    )

    role = UserRepository().get_role(uid)

    request.state.uid = uid
    request.state.role = role
    request.state.sign_in_provider = sign_in_provider

    return UserContext(uid=uid, role=role)


async def get_optional_user(request: Request) -> UserContext | None:
    """FastAPI dependency for public endpoints that optionally recognize authenticated users."""
    token = _extract_bearer_token(request)
    if token is None:
        return None
    return _verify_token_to_context(request, token)


async def require_auth(request: Request) -> UserContext:
    """FastAPI dependency for authenticated routes. Rejects missing or invalid tokens with 401."""
    token = _extract_bearer_token(request)
    if token is None:
        raise InvalidTokenError()
    return _verify_token_to_context(request, token)


async def require_admin(user: UserContext = Depends(require_auth)) -> UserContext:
    """FastAPI dependency for admin-only routes. Rejects non-admin users with 403."""
    if user.role != "admin":
        raise ForbiddenError()
    return user
