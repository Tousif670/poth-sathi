from functools import cmp_to_key
from typing import Literal

from app.core.cache import TTLCache, public_data_cache
from app.core.errors import NotFoundError
from app.models.common import BilingualText
from app.models.hotel import HotelArea, HotelDoc, HotelListItem, HotelListResponse, HotelSort
from app.repositories.hotel_repository import HotelRepository

HOTELS_CACHE_KEY = "hotels:all"


class HotelNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__(
            code="HOTEL_NOT_FOUND",
            message_bn="কাঙ্ক্ষিত হোটেলটি খুঁজে পাওয়া যায়নি।",
            message_en="The requested hotel could not be found.",
        )


def compute_hotel_match_score(
    hotel: HotelDoc,
    area: HotelArea | None = None,
    max_price_bdt: float | None = None,
    requested_amenities: list[str] | None = None,
) -> float:
    """Compute recommender match score per docs/ai-spec.md §8.

    Formula:
        score = (budget_score * 0.30) + (area_score * 0.25)
              + (amenity_score * 0.25) + (rating_score * 0.20)
    """
    # 1. Budget score (weight 0.30)
    if max_price_bdt is None or max_price_bdt <= 0:
        budget_score = 1.0
    else:
        effective_price = float(hotel.price_min_bdt)
        if effective_price <= max_price_bdt:
            budget_score = 1.0 - (max_price_bdt - effective_price) / max_price_bdt
        else:
            budget_score = 0.0

    # 2. Area match (weight 0.25)
    if area is None:
        area_score = 1.0
    elif hotel.area == area:
        area_score = 1.0
    else:
        area_score = 0.0

    # 3. Amenity overlap (weight 0.25)
    clean_requested = [a.strip().lower() for a in (requested_amenities or []) if a.strip()]
    if not clean_requested:
        amenity_score = 1.0
    else:
        hotel_set = {a.strip().lower() for a in hotel.amenities}
        matched = sum(1 for req in clean_requested if req in hotel_set)
        amenity_score = matched / len(clean_requested)

    # 4. Rating score (weight 0.20)
    if hotel.rating is None or hotel.rating <= 0:
        rating_score = 0.5
    else:
        rating_score = min(max(float(hotel.rating) / 5.0, 0.0), 1.0)

    score = (
        (budget_score * 0.30)
        + (area_score * 0.25)
        + (amenity_score * 0.25)
        + (rating_score * 0.20)
    )
    return round(score, 3)


def _compare_ranked_hotels(a: HotelListItem, b: HotelListItem) -> int:
    """Sort descending by match_score with 0.01 tie-break rules (ai-spec.md §8).

    If scores are within 0.01:
      1. is_verified (True before False)
      2. rating (higher before lower)
      3. name (alphabetical ascending)
    """
    diff = b.match_score - a.match_score
    if abs(diff) > 0.01:
        return 1 if diff > 0 else -1

    if a.is_verified != b.is_verified:
        return -1 if a.is_verified else 1

    if a.rating != b.rating:
        return 1 if b.rating > a.rating else -1

    if a.name != b.name:
        return -1 if a.name < b.name else 1

    return 0


def _pick_lang(text: BilingualText | None, lang: Literal["bn", "en"]) -> str | None:
    if text is None:
        return None
    return text.bn if lang == "bn" else text.en


class HotelService:
    """Service layer for hotel filtering, recommendation scoring, and caching."""

    def __init__(
        self,
        repository: HotelRepository | None = None,
        cache: TTLCache[object] | None = None,
    ) -> None:
        self._repo = repository if repository is not None else HotelRepository()
        self._cache = cache if cache is not None else public_data_cache

    def _get_all_hotels(self) -> list[HotelDoc]:
        cached = self._cache.get(HOTELS_CACHE_KEY)
        if isinstance(cached, list):
            return cached
        hotels = self._repo.list_all()
        self._cache.set(HOTELS_CACHE_KEY, hotels)
        return hotels

    def _to_item(
        self,
        doc: HotelDoc,
        lang: Literal["bn", "en"],
        score: float,
    ) -> HotelListItem:
        return HotelListItem(
            hotel_id=doc.hotel_id or doc.id,
            name=_pick_lang(doc.name, lang) or doc.name.en,
            name_bilingual=doc.name,
            area=doc.area,
            description=_pick_lang(doc.description, lang),
            description_bilingual=doc.description,
            address=_pick_lang(doc.address, lang),
            address_bilingual=doc.address,
            price_min_bdt=doc.price_min_bdt,
            price_max_bdt=doc.price_max_bdt,
            amenities=doc.amenities,
            rating=float(doc.rating or 0.0),
            phone=doc.phone,
            lat=doc.lat,
            lon=doc.lon,
            image_url=doc.image_url,
            data_source=doc.data_source,
            is_verified=doc.is_verified,
            last_updated=doc.last_updated,
            match_score=score,
        )

    def search_hotels(
        self,
        area: HotelArea | None = None,
        max_price_bdt: float | None = None,
        amenities: list[str] | None = None,
        sort: HotelSort = "match",
        lang: Literal["bn", "en"] = "bn",
        limit: int = 10,
        offset: int = 0,
        strict_filter: bool = True,
    ) -> HotelListResponse:
        all_hotels = self._get_all_hotels()
        clean_amenities = [a.strip().lower() for a in (amenities or []) if a.strip()]

        items: list[HotelListItem] = []
        for doc in all_hotels:
            if strict_filter:
                if area is not None and doc.area != area:
                    continue
                if max_price_bdt is not None and float(doc.price_min_bdt) > max_price_bdt:
                    continue

            score = compute_hotel_match_score(
                hotel=doc,
                area=area,
                max_price_bdt=max_price_bdt,
                requested_amenities=clean_amenities,
            )
            items.append(self._to_item(doc, lang=lang, score=score))

        if sort == "price_asc":
            items.sort(key=lambda h: (float(h.price_min_bdt), -h.match_score))
        elif sort == "price_desc":
            items.sort(key=lambda h: (-float(h.price_min_bdt), -h.match_score))
        elif sort == "rating":
            items.sort(key=lambda h: (-h.rating, -h.match_score))
        else:
            items.sort(key=cmp_to_key(_compare_ranked_hotels))

        total = len(items)
        sliced = items[offset : offset + limit]
        return HotelListResponse(items=sliced, total=total, limit=limit, offset=offset)

    def get_hotel(self, hotel_id: str, lang: Literal["bn", "en"] = "bn") -> HotelListItem:
        for doc in self._get_all_hotels():
            if doc.hotel_id == hotel_id or doc.id == hotel_id:
                score = compute_hotel_match_score(doc)
                return self._to_item(doc, lang=lang, score=score)

        direct = self._repo.get_by_id(hotel_id)
        if direct is None:
            raise HotelNotFoundError()
        score = compute_hotel_match_score(direct)
        return self._to_item(direct, lang=lang, score=score)
