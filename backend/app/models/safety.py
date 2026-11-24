from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.common import BilingualText, MetadataMixin


class BeachStatusDoc(MetadataMixin):
    id: str = ""
    zone_id: Literal["kolatoli", "sugandha", "laboni"] = "kolatoli"  # D23
    zone_name: BilingualText
    flag_colour: Literal["green", "yellow", "red"]
    note: BilingualText | None = None
    set_by: str = "admin"

    @model_validator(mode="after")
    def sync_id_and_zone_id(self) -> "BeachStatusDoc":
        if not self.id and self.zone_id:
            self.id = self.zone_id
        elif not self.zone_id and self.id:
            self.zone_id = self.id  # type: ignore
        return self


class EmergencyContactDoc(BaseModel):
    id: str = ""
    service: BilingualText
    number: str
    status: str = "TO_VERIFY"


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
