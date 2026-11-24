from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.models.transport import FareCalculationResponse, FareRouteListResponse
from app.services.transport_service import TransportService

router = APIRouter()


def get_transport_service() -> TransportService:
    return TransportService()


@router.get("/transport/fares", response_model=FareRouteListResponse)
async def list_transport_fares(
    origin: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: TransportService = Depends(get_transport_service),
) -> FareRouteListResponse:
    """Fetch verified local transport routes and fare ranges."""
    return service.list_fares(origin=origin, destination=destination, mode=mode, lang=lang)


@router.get("/transport/calculate", response_model=FareCalculationResponse)
async def calculate_transport_fare(
    origin: str = Query(..., min_length=1),
    destination: str = Query(..., min_length=1),
    mode: str | None = Query(default=None),
    passengers: int = Query(default=1, ge=1, le=20),
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: TransportService = Depends(get_transport_service),
) -> FareCalculationResponse:
    """Calculate estimated fare for a route and passenger count (D22)."""
    return service.calculate_fare(
        origin=origin,
        destination=destination,
        mode=mode,
        passengers=passengers,
        lang=lang,
    )
