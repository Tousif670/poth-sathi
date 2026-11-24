from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ChatLanguage = Literal["bn", "en"]
CardType = Literal["hotel", "place", "fare", "beach_status"]
SeverityLevel = Literal["info", "warning", "error"]


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    language: ChatLanguage | None = None


class ChatCard(BaseModel):
    type: CardType
    data: dict[str, Any]


class ChatSource(BaseModel):
    label: str
    source_id: str
    is_verified: bool = False


class ChatResponse(BaseModel):
    """Standard chat response conforming to docs/ai-spec.md §12."""

    answer_text: str
    language: ChatLanguage
    session_id: str | None = None
    cards: list[ChatCard] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)
    severity: SeverityLevel | None = None
    tool_calls_used: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    safety_triggered: bool = False
    is_ai_resting: bool = False


class ChatMessageDoc(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    language: ChatLanguage = "bn"
    created_at: datetime


class ChatSessionDoc(BaseModel):
    session_id: str
    uid: str
    language: ChatLanguage = "bn"
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class PaginatedChatSessions(BaseModel):
    items: list[ChatSessionDoc]
    total: int
    limit: int
    offset: int


class PaginatedChatMessages(BaseModel):
    items: list[ChatMessageDoc]
    total: int
    limit: int
    offset: int
