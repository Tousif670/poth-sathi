from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.models.hotel import HotelArea, HotelListItem, HotelListResponse, HotelSort
from app.services.hotel_service import HotelService

router = APIRouter()


def get_hotel_service() -> HotelService:
    return HotelService()


@router.get("/hotels", response_model=HotelListResponse)
async def list_hotels(
    area: HotelArea | None = Query(default=None),
    max_price_bdt: float | None = Query(default=None, gt=0),
    amenities: str | None = Query(
        default=None,
        description="Comma-separated list of desired amenities (e.g. wifi,pool)",
    ),
    sort: HotelSort = Query(default="match"),
    lang: Literal["bn", "en"] = Query(default="bn"),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    service: HotelService = Depends(get_hotel_service),
) -> HotelListResponse:
    """Browse and filter verified hotels with recommender match scoring."""
    amenity_list = [a.strip() for a in amenities.split(",") if a.strip()] if amenities else []
    return service.search_hotels(
        area=area,
        max_price_bdt=max_price_bdt,
        amenities=amenity_list,
        sort=sort,
        lang=lang,
        limit=limit,
        offset=offset,
    )


@router.get("/hotels/{hotel_id}", response_model=HotelListItem)
async def get_hotel_detail(
    hotel_id: str,
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: HotelService = Depends(get_hotel_service),
) -> HotelListItem:
    """Get detailed information for a specific hotel by ID."""
    return service.get_hotel(hotel_id=hotel_id, lang=lang)
