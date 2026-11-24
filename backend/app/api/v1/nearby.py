from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.models.place import NearbyResponse, PlaceFilterCategory
from app.services.nearby_service import NearbyService

router = APIRouter()


def get_nearby_service() -> NearbyService:
    return NearbyService()


@router.get("/nearby", response_model=NearbyResponse)
async def get_nearby_places(
    category: PlaceFilterCategory = Query(default="all"),
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    radius_km: float = Query(default=5.0, gt=0, le=50.0),
    lang: Literal["bn", "en"] = Query(default="bn"),
    limit: int = Query(default=20, ge=1, le=50),
    service: NearbyService = Depends(get_nearby_service),
) -> NearbyResponse:
    """Locate essential places (hospitals, pharmacies, police, ATMs, mosques) with distance."""
    return service.find_nearby(
        category=category,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        lang=lang,
        limit=limit,
    )
