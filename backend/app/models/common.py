from datetime import datetime

from pydantic import BaseModel, Field


class BilingualText(BaseModel):
    bn: str
    en: str


class MetadataMixin(BaseModel):
    data_source: str = "EXAMPLE"
    is_verified: bool = False
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class ErrorDetail(BaseModel):
    code: str
    message_bn: str
    message_en: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
