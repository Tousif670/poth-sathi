import uuid
from datetime import UTC, datetime

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1.client import Client

from app.core.errors import DatabaseUnavailableError
from app.core.firebase import get_firestore_client
from app.models.safety import BeachStatusDoc, BeachZoneId, FlagColour, SOSEventDoc

BEACH_STATUS_COLLECTION = "beach_status"
SOS_EVENTS_COLLECTION = "sos_events"


class SafetyRepository:
    """Firestore repository for beach_status/{zone_id} and sos_events/{sos_id}."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        return self._db if self._db is not None else get_firestore_client()

    def list_beach_status(self) -> list[BeachStatusDoc]:
        try:
            docs = list(self.db.collection(BEACH_STATUS_COLLECTION).stream())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        results: list[BeachStatusDoc] = []
        for snap in docs:
            data = snap.to_dict() or {}
            data.setdefault("id", snap.id)
            data.setdefault("zone_id", snap.id)
            results.append(BeachStatusDoc.model_validate(data))
        return results

    def update_beach_flag(
        self,
        zone_id: BeachZoneId,
        flag_colour: FlagColour,
        note_bn: str,
        note_en: str,
        set_by: str,
    ) -> BeachStatusDoc:
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        doc_ref = self.db.collection(BEACH_STATUS_COLLECTION).document(zone_id)
        try:
            snap = doc_ref.get()
            existing = snap.to_dict() if snap.exists else {}
            payload = {
                **(existing or {}),
                "id": zone_id,
                "zone_id": zone_id,
                "zone_name": (existing or {}).get(
                    "zone_name",
                    {"bn": zone_id, "en": zone_id.capitalize()},
                ),
                "flag_colour": flag_colour,
                "note": {"bn": note_bn, "en": note_en},
                "set_by": set_by,
                "last_updated": now_iso,
                "data_source": "admin_update",
                "is_verified": True,
            }
            doc_ref.set(payload)
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc

        return BeachStatusDoc.model_validate(payload)

    def create_sos_event(
        self,
        trigger_type: str,
        lat: float | None = None,
        lng: float | None = None,
        uid: str | None = None,
    ) -> SOSEventDoc:
        sos_id = f"sos_{uuid.uuid4().hex[:10]}"
        event = SOSEventDoc(
            sos_id=sos_id,
            uid=uid,
            trigger_type=trigger_type,  # type: ignore[arg-type]
            lat=lat,
            lng=lng,
            created_at=datetime.now(UTC),
        )
        try:
            self.db.collection(SOS_EVENTS_COLLECTION).document(sos_id).set(event.model_dump())
        except GoogleAPICallError as exc:
            raise DatabaseUnavailableError() from exc
        return event
