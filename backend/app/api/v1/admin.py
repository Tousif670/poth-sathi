from fastapi import APIRouter, Body, Depends, Query

from app.core.auth import require_admin
from app.models.admin import (
    AdminBeachFlagUpdateRequest,
    AdminBeachFlagUpdateResponse,
    AdminCacheRefreshRequest,
    AdminCacheRefreshResponse,
    PaginatedReportsResponse,
)
from app.models.safety import BeachZoneId
from app.models.user import UserContext
from app.services.admin_service import AdminService

router = APIRouter()


def get_admin_service() -> AdminService:
    return AdminService()


@router.put(
    "/admin/beach-status/{zone_id}",
    response_model=AdminBeachFlagUpdateResponse,
)
async def admin_update_beach_status(
    zone_id: BeachZoneId,
    payload: AdminBeachFlagUpdateRequest,
    admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminBeachFlagUpdateResponse:
    """Update beach hazard flag for a zone and invalidate backend cache (Admin only)."""
    return service.update_beach_status(zone_id=zone_id, payload=payload, admin_uid=admin.uid)


@router.post("/admin/cache/refresh", response_model=AdminCacheRefreshResponse)
async def admin_refresh_cache(
    payload: AdminCacheRefreshRequest = Body(default_factory=AdminCacheRefreshRequest),
    _admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminCacheRefreshResponse:
    """Clear in-memory TTL cache and rebuild RAG index (Admin only)."""
    return service.refresh_cache(scope=payload.scope)


@router.get("/admin/reports", response_model=PaginatedReportsResponse)
async def admin_list_reports(
    status: str = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin: UserContext = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedReportsResponse:
    """List user-submitted wrong-info reports (Admin only)."""
    return service.list_reports(status_filter=status, limit=limit, offset=offset)
