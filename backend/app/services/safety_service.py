from datetime import UTC, datetime, timedelta
from typing import Literal

from app.core.cache import TTLCache, public_data_cache
from app.models.common import BilingualText
from app.models.safety import (
    AdvisoriesResponse,
    AdvisoryItem,
    BeachStatusDoc,
    BeachStatusResponse,
    BeachZoneId,
    BeachZoneStatusItem,
    FlagColour,
)
from app.repositories.kb_repository import KBRepository
from app.repositories.safety_repository import SafetyRepository

BEACH_STATUS_CACHE_KEY = "beach_status:all"
ADVISORIES_CACHE_KEY = "safety_advisories:all"
OUTDATED_THRESHOLD_HOURS = 6  # D24: older than 6 hours shows "may be outdated"

FLAG_MEANINGS: dict[FlagColour, BilingualText] = {
    "green": BilingualText(
        bn="নিরাপদ সমুদ্র পরিস্থিতি। নির্ধারিত স্থানে সাঁতার কাটা নিরাপদ।",
        en="Low hazard. Calm conditions; swimming permitted in designated areas.",
    ),
    "yellow": BilingualText(
        bn="মাঝারি সতর্কতা। ঢেউ বা স্রোত থাকতে পারে; সাবধানে সাঁতার কাটুন।",
        en="Medium hazard. Rough surf or strong currents; swim with caution.",
    ),
    "red": BilingualText(
        bn="উচ্চ বিপদ! তীব্র স্রোত ও ঢেউ। সমুদ্রে নামা সম্পূর্ণ নিষিদ্ধ।",
        en="High hazard! Strong surf and currents. Do NOT enter the water.",
    ),
}


def is_beach_status_outdated(last_updated_iso: str, now: datetime | None = None) -> bool:
    """Return True if last_updated is older than 6 hours (D24)."""
    ref_now = now if now is not None else datetime.now(UTC)
    try:
        cleaned = last_updated_iso.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return (ref_now - parsed) > timedelta(hours=OUTDATED_THRESHOLD_HOURS)
    except Exception:
        return True


def _pick_lang(text: BilingualText | None, lang: Literal["bn", "en"]) -> str | None:
    if text is None:
        return None
    return text.bn if lang == "bn" else text.en


class SafetyService:
    """Service layer for multi-zone beach flag status (D23, D24) and safety advisories."""

    def __init__(
        self,
        safety_repository: SafetyRepository | None = None,
        kb_repository: KBRepository | None = None,
        cache: TTLCache[object] | None = None,
    ) -> None:
        self._safety_repo = (
            safety_repository if safety_repository is not None else SafetyRepository()
        )
        self._kb_repo = kb_repository if kb_repository is not None else KBRepository()
        self._cache = cache if cache is not None else public_data_cache

    def _get_all_zones(self) -> list[BeachStatusDoc]:
        cached = self._cache.get(BEACH_STATUS_CACHE_KEY)
        if isinstance(cached, list):
            return cached
        zones = self._safety_repo.list_beach_status()
        self._cache.set(BEACH_STATUS_CACHE_KEY, zones)
        return zones

    def get_beach_status(
        self,
        zone_id: BeachZoneId | None = None,
        lang: Literal["bn", "en"] = "bn",
        now: datetime | None = None,
    ) -> BeachStatusResponse:
        docs = self._get_all_zones()
        zone_order: dict[str, int] = {"kolatoli": 0, "sugandha": 1, "laboni": 2}
        docs_sorted = sorted(docs, key=lambda d: zone_order.get(d.zone_id, 99))

        items: list[BeachZoneStatusItem] = []
        for doc in docs_sorted:
            if zone_id is not None and doc.zone_id != zone_id:
                continue

            meaning_text = FLAG_MEANINGS.get(doc.flag_colour, FLAG_MEANINGS["yellow"])
            items.append(
                BeachZoneStatusItem(
                    zone_id=doc.zone_id,
                    zone_name=_pick_lang(doc.zone_name, lang) or doc.zone_name.en,
                    zone_name_bilingual=doc.zone_name,
                    flag=doc.flag_colour,
                    flag_colour=doc.flag_colour,
                    flag_meaning=_pick_lang(meaning_text, lang) or meaning_text.en,
                    note=_pick_lang(doc.note, lang),
                    note_bilingual=doc.note,
                    updated_by=doc.set_by,
                    data_source=doc.data_source,
                    is_verified=doc.is_verified,
                    last_updated=doc.last_updated,
                    is_outdated=is_beach_status_outdated(doc.last_updated, now=now),
                )
            )

        return BeachStatusResponse(zones=items)

    def get_advisories(self, lang: Literal["bn", "en"] = "bn") -> AdvisoriesResponse:
        cached = self._cache.get(ADVISORIES_CACHE_KEY)
        if isinstance(cached, list):
            chunks = cached
        else:
            chunks = self._kb_repo.list_all()
            self._cache.set(ADVISORIES_CACHE_KEY, chunks)

        items: list[AdvisoryItem] = []
        for chunk in chunks:
            if chunk.category != "beach_safety":
                continue
            items.append(
                AdvisoryItem(
                    chunk_id=chunk.chunk_id or chunk.id,
                    category=chunk.category,
                    text=_pick_lang(chunk.text, lang) or chunk.text.en,
                    text_bilingual=chunk.text,
                    data_source=chunk.data_source,
                    is_verified=chunk.is_verified,
                    last_updated=chunk.last_updated,
                )
            )

        return AdvisoriesResponse(items=items, count=len(items))
