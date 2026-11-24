from fastapi import APIRouter, Body, Depends, Request, Response, status

from app.core.auth import require_admin, require_auth
from app.models.user import RegisterRequest, UpdateProfileRequest, UserContext, UserProfile
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/auth/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    response: Response,
    payload: RegisterRequest = Body(default_factory=RegisterRequest),
    user: UserContext = Depends(require_auth),
    service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    """Idempotently register or sync the authenticated user's profile."""
    sign_in_provider = getattr(request.state, "sign_in_provider", None)
    profile, created = service.register(
        uid=user.uid,
        sign_in_provider=sign_in_provider,
        payload=payload,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return profile


@router.get("/me", response_model=UserProfile)
async def get_me(
    user: UserContext = Depends(require_auth),
    service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    """Return the authenticated user's profile."""
    return service.get_me(user.uid)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    payload: UpdateProfileRequest,
    user: UserContext = Depends(require_auth),
    service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    """Update the authenticated user's display_name and/or preferred_language."""
    return service.update_me(user.uid, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: UserContext = Depends(require_auth),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    """Delete the authenticated user's profile and usage records."""
    service.delete_me(user.uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# TODO(Slice 8): Replace this temporary admin ping route with the full admin router.
@router.get("/admin/ping")
async def admin_ping(
    _admin: UserContext = Depends(require_admin),
) -> dict[str, bool]:
    """Temporary admin-only endpoint for verifying role-based access control."""
    return {"ok": True}
