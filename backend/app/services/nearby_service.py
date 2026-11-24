import math
from typing import Literal

from app.core.cache import TTLCache, public_data_cache
from app.core.errors import InvalidInputError
from app.models.common import BilingualText
from app.models.place import NearbyResponse, PlaceDoc, PlaceFilterCategory, PlaceListItem
from app.repositories.place_repository import PlaceRepository

PLACES_CACHE_KEY = "places:all"
EARTH_RADIUS_KM = 6371.0


class InvalidCoordinatesError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_COORDINATES",
            message_bn="অক্ষাংশ বা দ্রাঘিমাংশ সঠিক নয়।",
            message_en="Invalid latitude or longitude coordinates.",
        )


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometers between two GPS points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def _pick_lang(text: BilingualText | None, lang: Literal["bn", "en"]) -> str | None:
    if text is None:
        return None
    return text.bn if lang == "bn" else text.en


class NearbyService:
    """Service layer for finding nearby essential places with haversine distance filtering."""

    def __init__(
        self,
        repository: PlaceRepository | None = None,
        cache: TTLCache[object] | None = None,
    ) -> None:
        self._repo = repository if repository is not None else PlaceRepository()
        self._cache = cache if cache is not None else public_data_cache

    def _get_all_places(self) -> list[PlaceDoc]:
        cached = self._cache.get(PLACES_CACHE_KEY)
        if isinstance(cached, list):
            return cached
        places = self._repo.list_all()
        self._cache.set(PLACES_CACHE_KEY, places)
        return places

    def find_nearby(
        self,
        category: PlaceFilterCategory = "all",
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float = 5.0,
        lang: Literal["bn", "en"] = "bn",
        limit: int = 20,
    ) -> NearbyResponse:
        if (lat is not None and not (-90.0 <= lat <= 90.0)) or (
            lng is not None and not (-180.0 <= lng <= 180.0)
        ):
            raise InvalidCoordinatesError()

        places = self._get_all_places()
        items: list[PlaceListItem] = []

        for doc in places:
            if category != "all" and doc.category != category:
                continue

            dist_km: float | None = None
            if lat is not None and lng is not None:
                dist_km = haversine_distance_km(lat, lng, doc.lat, doc.lon)
                if dist_km > radius_km:
                    continue

            items.append(
                PlaceListItem(
                    place_id=doc.place_id or doc.id,
                    name=_pick_lang(doc.name, lang) or doc.name.en,
                    name_bilingual=doc.name,
                    category=doc.category,
                    description=_pick_lang(doc.description, lang),
                    description_bilingual=doc.description,
                    address=_pick_lang(doc.address, lang),
                    address_bilingual=doc.address,
                    phone=doc.phone,
                    opening_hours=doc.opening_hours,
                    lat=doc.lat,
                    lon=doc.lon,
                    distance_km=dist_km,
                    data_source=doc.data_source,
                    is_verified=doc.is_verified,
                    last_updated=doc.last_updated,
                )
            )

        if lat is not None and lng is not None:
            items.sort(key=lambda p: (p.distance_km if p.distance_km is not None else 9999.0))

        sliced = items[:limit]
        return NearbyResponse(items=sliced, count=len(sliced))
