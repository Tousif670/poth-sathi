from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import BilingualText
from app.models.safety import BeachZoneId, FlagColour

ReportEntityType = Literal["hotel", "place", "transport_route"]
ReportStatus = Literal["pending", "reviewed"]


class ReportCreateRequest(BaseModel):
    entity_type: ReportEntityType
    entity_id: str = Field(..., min_length=1)
    issue_description: str = Field(..., min_length=3, max_length=1000)
    reported_by_uid: str | None = None


class ReportDoc(BaseModel):
    report_id: str
    entity_type: ReportEntityType
    entity_id: str
    issue_description: str
    reported_by_uid: str | None = None
    status: ReportStatus = "pending"
    created_at: datetime


class ReportSubmissionResponse(BaseModel):
    report_id: str
    status: ReportStatus = "pending"
    message_en: str = "Thank you. Your report has been submitted for administrative review."
    message_bn: str = "ধন্যবাদ। আপনার প্রতিবেদনটি পর্যালোচনার জন্য জমা হয়েছে।"


class PaginatedReportsResponse(BaseModel):
    items: list[ReportDoc]
    total: int
    limit: int
    offset: int


class AdminBeachFlagUpdateRequest(BaseModel):
    flag: FlagColour
    flag_meaning: BilingualText | None = None


class AdminBeachFlagUpdateResponse(BaseModel):
    zone_id: BeachZoneId
    flag: FlagColour
    last_updated: str
    updated_by: str


class AdminCacheRefreshRequest(BaseModel):
    scope: Literal["all", "hotels", "places", "fares", "kb"] = "all"


class AdminCacheRefreshResponse(BaseModel):
    status: str = "reloaded"
    timestamp: str
