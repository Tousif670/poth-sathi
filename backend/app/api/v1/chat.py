from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.auth import get_optional_user, require_auth
from app.models.chat import ChatRequest, ChatResponse, PaginatedChatSessions
from app.models.user import UserContext
from app.services.chat_service import ChatService

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/chat/messages", response_model=ChatResponse)
async def post_chat_message(
    request: Request,
    response: Response,
    payload: ChatRequest,
    user: UserContext | None = Depends(get_optional_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Process a bilingual chat message with PII stripping, rate limits, and Gemini wrapper."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    uid = user.uid if user is not None else None
    chat_res, rl = await service.process_message(
        payload=payload,
        uid=uid,
        client_ip=client_ip,
    )
    response.headers["X-RateLimit-Limit"] = str(rl.limit)
    response.headers["X-RateLimit-Remaining"] = str(rl.remaining)
    response.headers["X-RateLimit-Reset"] = str(rl.reset_epoch)
    return chat_res


@router.get("/chat/sessions", response_model=PaginatedChatSessions)
async def list_chat_sessions(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: UserContext = Depends(require_auth),
    service: ChatService = Depends(get_chat_service),
) -> PaginatedChatSessions:
    """List saved chat sessions for the authenticated tourist."""
    data = service.get_sessions(uid=user.uid, limit=limit, offset=offset)
    return PaginatedChatSessions.model_validate(data)
