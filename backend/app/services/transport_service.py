from typing import Literal

from app.core.cache import TTLCache, public_data_cache
from app.core.errors import InvalidInputError
from app.models.common import BilingualText
from app.models.transport import (
    FareCalculationResponse,
    FareRouteItem,
    FareRouteListResponse,
    RouteDoc,
)
from app.repositories.transport_repository import TransportRepository

ROUTES_CACHE_KEY = "transport_routes:all"

LOCATION_ALIASES: dict[str, list[str]] = {
    "kolatoli": ["kolatoli", "কলাতলী"],
    "sugandha": ["sugandha", "সুগন্ধা"],
    "laboni": ["laboni", "লাবণী"],
}

MODE_ALIASES: dict[str, list[str]] = {
    "cng": ["cng", "cng_auto", "auto"],
    "cng_auto": ["cng", "cng_auto", "auto"],
    "tomtom": ["tomtom", "easybike", "ইজিবাইক", "টমটম"],
    "rickshaw": ["rickshaw", "রিকশা"],
}


class RouteNotFoundError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__(
            code="ROUTE_NOT_FOUND",
            message_bn="এই রুটের জন্য কোনো যাচাইকৃত ভাড়ার তথ্য পাওয়া যায়নি।",
            message_en="No verified transport route found for the selected origin and destination.",
        )


def _matches_location(query: str, text: BilingualText) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    haystack = f"{text.en.lower()} {text.bn.lower()}"
    if q in haystack:
        return True
    for key, tokens in LOCATION_ALIASES.items():
        if q == key or any(tok in q for tok in tokens):
            if any(tok in haystack for tok in tokens):
                return True
    return False


def _matches_mode(mode_query: str | None, vehicle_type: str) -> bool:
    if not mode_query:
        return True
    q = mode_query.strip().lower()
    vt = vehicle_type.strip().lower()
    if q == vt or q in vt or vt in q:
        return True
    aliases = MODE_ALIASES.get(q, [])
    return vt in aliases


def _pick_lang(text: BilingualText | None, lang: Literal["bn", "en"]) -> str | None:
    if text is None:
        return None
    return text.bn if lang == "bn" else text.en


class TransportService:
    """Service layer for transport routes lookup and D22 fare calculation."""

    def __init__(
        self,
        repository: TransportRepository | None = None,
        cache: TTLCache[object] | None = None,
    ) -> None:
        self._repo = repository if repository is not None else TransportRepository()
        self._cache = cache if cache is not None else public_data_cache

    def _get_all_routes(self) -> list[RouteDoc]:
        cached = self._cache.get(ROUTES_CACHE_KEY)
        if isinstance(cached, list):
            return cached
        routes = self._repo.list_all()
        self._cache.set(ROUTES_CACHE_KEY, routes)
        return routes

    def list_fares(
        self,
        origin: str | None = None,
        destination: str | None = None,
        mode: str | None = None,
        lang: Literal["bn", "en"] = "bn",
    ) -> FareRouteListResponse:
        routes = self._get_all_routes()
        items: list[FareRouteItem] = []

        for doc in routes:
            if origin and not _matches_location(origin, doc.origin):
                continue
            if destination and not _matches_location(destination, doc.destination):
                continue
            if mode and not _matches_mode(mode, doc.vehicle_type):
                continue

            items.append(
                FareRouteItem(
                    route_id=doc.route_id or doc.id,
                    origin=_pick_lang(doc.origin, lang) or doc.origin.en,
                    origin_bilingual=doc.origin,
                    destination=_pick_lang(doc.destination, lang) or doc.destination.en,
                    destination_bilingual=doc.destination,
                    vehicle_type=doc.vehicle_type,
                    fare_basis=doc.fare_basis,
                    fare_min_bdt=doc.fare_min_bdt,
                    fare_max_bdt=doc.fare_max_bdt,
                    distance_km=doc.distance_km,
                    notes=_pick_lang(doc.notes, lang),
                    notes_bilingual=doc.notes,
                    data_source=doc.data_source,
                    is_verified=doc.is_verified,
                    last_updated=doc.last_updated,
                )
            )

        return FareRouteListResponse(items=items, count=len(items))

    def calculate_fare(
        self,
        origin: str,
        destination: str,
        mode: str | None = None,
        passengers: int = 1,
        lang: Literal["bn", "en"] = "bn",
    ) -> FareCalculationResponse:
        """Calculate fare per D22: passengers multiplies fare only when fare_basis == per_person."""
        if passengers < 1:
            raise InvalidInputError()

        routes = self._get_all_routes()
        matched: RouteDoc | None = None

        for doc in routes:
            forward = _matches_location(origin, doc.origin) and _matches_location(
                destination, doc.destination
            )
            reverse = _matches_location(origin, doc.destination) and _matches_location(
                destination, doc.origin
            )
            if (forward or reverse) and _matches_mode(mode, doc.vehicle_type):
                matched = doc
                break

        if matched is None:
            raise RouteNotFoundError()

        multiplier = passengers if matched.fare_basis == "per_person" else 1
        min_fare = matched.fare_min_bdt * multiplier
        max_fare = matched.fare_max_bdt * multiplier
        dist_km = float(matched.distance_km or 2.0)
        est_minutes = max(5, round(dist_km * 4.5))

        return FareCalculationResponse(
            origin=_pick_lang(matched.origin, lang) or matched.origin.en,
            destination=_pick_lang(matched.destination, lang) or matched.destination.en,
            mode=matched.vehicle_type,
            passengers=passengers,
            fare_basis=matched.fare_basis,
            min_fare_bdt=min_fare,
            max_fare_bdt=max_fare,
            estimated_time_min=est_minutes,
            distance_km=dist_km,
            route_id=matched.route_id or matched.id,
            notes=_pick_lang(matched.notes, lang),
            data_source=matched.data_source,
            is_verified=matched.is_verified,
            last_updated=matched.last_updated,
        )
