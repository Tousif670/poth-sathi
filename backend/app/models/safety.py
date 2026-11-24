from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.common import BilingualText, MetadataMixin

BeachZoneId = Literal["kolatoli", "sugandha", "laboni"]
FlagColour = Literal["green", "yellow", "red"]


class BeachStatusDoc(MetadataMixin):
    id: str = ""
    zone_id: BeachZoneId = "kolatoli"  # D23
    zone_name: BilingualText
    flag_colour: FlagColour
    note: BilingualText | None = None
    set_by: str = "admin"

    @model_validator(mode="after")
    def sync_id_and_zone_id(self) -> "BeachStatusDoc":
        if not self.id and self.zone_id:
            self.id = self.zone_id
        elif not self.zone_id and self.id:
            self.zone_id = self.id  # type: ignore
        return self


class BeachZoneStatusItem(MetadataMixin):
    zone_id: BeachZoneId
    zone_name: str
    zone_name_bilingual: BilingualText
    flag: FlagColour
    flag_colour: FlagColour
    flag_meaning: str
    note: str | None = None
    note_bilingual: BilingualText | None = None
    updated_by: str
    is_outdated: bool = False


class BeachStatusResponse(BaseModel):
    zones: list[BeachZoneStatusItem]


class AdvisoryItem(MetadataMixin):
    chunk_id: str
    category: str
    text: str
    text_bilingual: BilingualText


class AdvisoriesResponse(BaseModel):
    items: list[AdvisoryItem]
    count: int


class EmergencyContactDoc(BaseModel):
    id: str = ""
    service: BilingualText
    number: str
    status: str = "TO_VERIFY"


class EmergencyContactItem(BaseModel):
    id: str
    service: str
    service_bilingual: BilingualText
    number: str
    status: str = "TO_VERIFY"
    tel_link: str


class EmergencyContactListResponse(BaseModel):
    items: list[EmergencyContactItem]
    count: int


class SOSRequest(BaseModel):
    lat: float | None = None
    lng: float | None = None
    trigger_type: Literal["button", "voice"] = "button"
    lang: Literal["bn", "en"] = "bn"


class SOSEventDoc(BaseModel):
    sos_id: str
    uid: str | None = None
    trigger_type: Literal["button", "voice"] = "button"
    lat: float | None = None
    lng: float | None = None
    created_at: datetime


class SOSQuickLinks(BaseModel):
    tel: str
    whatsapp: str


class SOSResponse(BaseModel):
    sos_id: str
    status: str = "logged"
    national_emergency: str = "999"
    tourist_police: str = "TO_VERIFY"
    ambulance: str = "199"
    guidance: str
    quick_links: SOSQuickLinks


class SafetyRuleItem(BaseModel):
    category: str
    keywords_bn: list[str] = Field(default_factory=list)
    keywords_en: list[str] = Field(default_factory=list)
    keywords_banglish: list[str] = Field(default_factory=list)
    action: str = "EMERGENCY"
    response_key: str
    status: str = "REVIEW"


class SafetyRulesDoc(BaseModel):
    rules: list[SafetyRuleItem]
