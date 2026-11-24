import json
from pathlib import Path
from typing import Literal

from app.models.safety import (
    EmergencyContactDoc,
    EmergencyContactItem,
    EmergencyContactListResponse,
    SOSQuickLinks,
    SOSRequest,
    SOSResponse,
)
from app.repositories.safety_repository import SafetyRepository
from app.services.nearby_service import InvalidCoordinatesError

SEED_EMERGENCY_CONTACTS_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "seed" / "emergency_contacts.json"
)


def _load_seed_emergency_contacts() -> list[EmergencyContactDoc]:
    if not SEED_EMERGENCY_CONTACTS_PATH.exists():
        return []
    raw = json.loads(SEED_EMERGENCY_CONTACTS_PATH.read_text(encoding="utf-8"))
    return [EmergencyContactDoc.model_validate(item) for item in raw]


class EmergencyService:
    """Service layer for emergency directory contacts and SOS event logging (D13, D14)."""

    def __init__(self, safety_repository: SafetyRepository | None = None) -> None:
        self._safety_repo = (
            safety_repository if safety_repository is not None else SafetyRepository()
        )

    def list_contacts(self, lang: Literal["bn", "en"] = "bn") -> EmergencyContactListResponse:
        docs = _load_seed_emergency_contacts()
        items: list[EmergencyContactItem] = []

        for doc in docs:
            label = doc.service.bn if lang == "bn" else doc.service.en
            dial = doc.number if doc.number.isdigit() else "999"
            items.append(
                EmergencyContactItem(
                    id=doc.id,
                    service=label,
                    service_bilingual=doc.service,
                    number=doc.number,
                    status=doc.status,
                    tel_link=f"tel:{dial}",
                )
            )

        return EmergencyContactListResponse(items=items, count=len(items))

    def trigger_sos(
        self,
        payload: SOSRequest,
        uid: str | None = None,
    ) -> SOSResponse:
        if (payload.lat is not None and not (-90.0 <= payload.lat <= 90.0)) or (
            payload.lng is not None and not (-180.0 <= payload.lng <= 180.0)
        ):
            raise InvalidCoordinatesError()

        event = self._safety_repo.create_sos_event(
            trigger_type=payload.trigger_type,
            lat=payload.lat,
            lng=payload.lng,
            uid=uid,
        )

        guidance = (
            "শান্ত থাকুন। অবিলম্বে ৯৯৯ নম্বরে কল করুন এবং আপনার অবস্থান ট্যুরিস্ট পুলিশকে জানান।"
            if payload.lang == "bn"
            else (
                "Please stay calm. Call 999 immediately and share your location "
                "with Tourist Police or lifeguards."
            )
        )

        return SOSResponse(
            sos_id=event.sos_id,
            status="logged",
            national_emergency="999",
            tourist_police="TO_VERIFY",
            ambulance="199",
            guidance=guidance,
            quick_links=SOSQuickLinks(
                tel="tel:999",
                whatsapp="https://wa.me/?text=Emergency%20SOS%20at%20Cox%27s%20Bazar",
            ),
        )
