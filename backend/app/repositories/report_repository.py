import uuid
from datetime import UTC, datetime

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.admin import ReportCreateRequest, ReportDoc

REPORTS_COLLECTION = "reports"


class ReportRepository:
    """Firestore repository for reports/{report_id} documents."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def create(
        self,
        payload: ReportCreateRequest,
        uid: str | None = None,
    ) -> ReportDoc:
        report_id = f"rep_{uuid.uuid4().hex[:10]}"
        doc = ReportDoc(
            report_id=report_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            issue_description=payload.issue_description,
            reported_by_uid=uid or payload.reported_by_uid,
            status="pending",
            created_at=datetime.now(UTC),
        )
        try:
            self.db.collection(REPORTS_COLLECTION).document(report_id).set(doc.model_dump())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return doc

    def list_all(self, status_filter: str | None = None) -> list[ReportDoc]:
        try:
            snaps = list(self.db.collection(REPORTS_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[ReportDoc] = []
        for snap in snaps:
            data = snap.to_dict() or {}
            data.setdefault("report_id", snap.id)
            doc = ReportDoc.model_validate(data)
            if status_filter and status_filter != "all" and doc.status != status_filter:
                continue
            results.append(doc)
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results
