from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_optional_user
from app.models.safety import EmergencyContactListResponse, SOSRequest, SOSResponse
from app.models.user import UserContext
from app.services.emergency_service import EmergencyService

router = APIRouter()


def get_emergency_service() -> EmergencyService:
    return EmergencyService()


@router.get("/emergency/contacts", response_model=EmergencyContactListResponse)
async def get_emergency_contacts(
    lang: Literal["bn", "en"] = Query(default="bn"),
    service: EmergencyService = Depends(get_emergency_service),
) -> EmergencyContactListResponse:
    """Return verified/seed emergency contact numbers (999, Tourist Police, Fire, Hospital)."""
    return service.list_contacts(lang=lang)


@router.post("/emergency/sos", response_model=SOSResponse, status_code=status.HTTP_201_CREATED)
async def create_sos_alert(
    payload: SOSRequest,
    user: UserContext | None = Depends(get_optional_user),
    service: EmergencyService = Depends(get_emergency_service),
) -> SOSResponse:
    """Log an SOS emergency event and return immediate 999 / WhatsApp quick links."""
    uid = user.uid if user is not None else None
    return service.trigger_sos(payload=payload, uid=uid)
