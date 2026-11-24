from datetime import UTC, datetime

from app.core.cache import TTLCache, public_data_cache
from app.models.admin import (
    AdminBeachFlagUpdateRequest,
    AdminBeachFlagUpdateResponse,
    AdminCacheRefreshResponse,
    PaginatedReportsResponse,
    ReportCreateRequest,
    ReportSubmissionResponse,
)
from app.models.safety import BeachZoneId
from app.repositories.report_repository import ReportRepository
from app.repositories.safety_repository import SafetyRepository
from app.services.rag_service import RAGService, global_rag_service
from app.services.safety_service import FLAG_MEANINGS


class AdminService:
    """Service layer for admin beach flag updates, cache invalidation, and user reports."""

    def __init__(
        self,
        safety_repository: SafetyRepository | None = None,
        report_repository: ReportRepository | None = None,
        cache: TTLCache[object] | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self._safety_repo = (
            safety_repository if safety_repository is not None else SafetyRepository()
        )
        self._report_repo = (
            report_repository if report_repository is not None else ReportRepository()
        )
        self._cache = cache if cache is not None else public_data_cache
        self._rag = rag_service if rag_service is not None else global_rag_service

    def update_beach_status(
        self,
        zone_id: BeachZoneId,
        payload: AdminBeachFlagUpdateRequest,
        admin_uid: str,
    ) -> AdminBeachFlagUpdateResponse:
        meaning = payload.flag_meaning or FLAG_MEANINGS[payload.flag]
        updated = self._safety_repo.update_beach_flag(
            zone_id=zone_id,
            flag_colour=payload.flag,
            note_bn=meaning.bn,
            note_en=meaning.en,
            set_by=admin_uid,
        )
        self._cache.clear()
        return AdminBeachFlagUpdateResponse(
            zone_id=updated.zone_id,
            flag=updated.flag_colour,
            last_updated=updated.last_updated,
            updated_by=updated.set_by,
        )

    def refresh_cache(self, scope: str = "all") -> AdminCacheRefreshResponse:
        self._cache.clear()
        if scope in ("all", "kb"):
            self._rag.rebuild_index()
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return AdminCacheRefreshResponse(status="reloaded", timestamp=now_iso)

    def submit_report(
        self,
        payload: ReportCreateRequest,
        uid: str | None = None,
    ) -> ReportSubmissionResponse:
        doc = self._report_repo.create(payload=payload, uid=uid)
        return ReportSubmissionResponse(report_id=doc.report_id, status=doc.status)

    def list_reports(
        self,
        status_filter: str = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedReportsResponse:
        docs = self._report_repo.list_all(status_filter=status_filter)
        return PaginatedReportsResponse(
            items=docs[offset : offset + limit],
            total=len(docs),
            limit=limit,
            offset=offset,
        )
