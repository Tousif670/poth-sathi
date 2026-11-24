import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.firebase import check_firestore_connection
from app.core.rate_limiter import current_dhaka_date, global_rate_limiter
from app.services.rag_service import global_rag_service

router = APIRouter()
_STARTUP_TIME = time.monotonic()


class HealthCheckResponse(BaseModel):
    status: str
    app_env: str
    environment: str
    firestore: str
    rag_chunks: int
    ai_quota_remaining: int
    uptime_sec: int


@router.get("/health", response_model=HealthCheckResponse)
async def get_health() -> dict[str, Any]:
    """Returns application health, environment, RAG status, and quota without secrets."""
    settings = get_settings()
    is_fs_ok = check_firestore_connection(timeout_seconds=1.5)
    firestore_status = "ok" if is_fs_ok else "down"

    date_str = current_dhaka_date()
    used_ai = global_rate_limiter._global_ai_counts.get(date_str, 0)
    remaining_ai = max(0, global_rate_limiter.global_daily_ai_limit - used_ai)

    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "environment": settings.APP_ENV,
        "firestore": firestore_status,
        "rag_chunks": len(global_rag_service._chunks),
        "ai_quota_remaining": remaining_ai,
        "uptime_sec": max(0, int(time.monotonic() - _STARTUP_TIME)),
    }
