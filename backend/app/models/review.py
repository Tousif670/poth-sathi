from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SentimentPolarity = Literal["positive", "negative", "neutral"]


class AspectScore(BaseModel):
    sentiment: SentimentPolarity = "neutral"
    positive: int = 0
    negative: int = 0


class SentimentResult(BaseModel):
    overall: SentimentPolarity
    confidence: float
    aspects: dict[str, AspectScore]


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=1000)
    lang: Literal["bn", "en"] = "bn"


class ReviewDoc(BaseModel):
    review_id: str
    hotel_id: str
    uid: str
    rating: int
    comment: str
    created_at: datetime
    sentiment: SentimentResult


class PaginatedReviewsResponse(BaseModel):
    items: list[ReviewDoc]
    total: int
    limit: int
    offset: int
