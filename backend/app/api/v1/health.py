from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.firebase import check_firestore_connection

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    app_env: str
    firestore: str


@router.get("/health", response_model=HealthCheckResponse)
async def get_health() -> dict[str, Any]:
    """Returns application health, environment, and firestore status without secrets."""
    settings = get_settings()
    is_fs_ok = check_firestore_connection(timeout_seconds=1.5)
    firestore_status = "ok" if is_fs_ok else "down"

    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "firestore": firestore_status,
    }
