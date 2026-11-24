from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.models.safety import AdvisoriesResponse, BeachStatusResponse, BeachZoneId
from app.services.safety_service import SafetyService

router = APIRouter()


def get_safety_service() -> SafetyService:
    return SafetyService()


@router.get("/safety/beach-status", response_model=BeachStatusResponse)
async def get_beach_status(
    zone_id: BeachZoneId | None = Query(default=None),
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: SafetyService = Depends(get_safety_service),
) -> BeachStatusResponse:
    """Get multi-zone beach safety flag status (D23, D24)."""
    return service.get_beach_status(zone_id=zone_id, lang=lang)


@router.get("/safety/advisories", response_model=AdvisoriesResponse)
async def get_safety_advisories(
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: SafetyService = Depends(get_safety_service),
) -> AdvisoriesResponse:
    """Get beach safety advisories from curated knowledge base."""
    return service.get_advisories(lang=lang)
