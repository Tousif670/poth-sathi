import re
from typing import Any

from app.core.errors import InputTooLongError, InvalidInputError
from app.core.llm_client import LLMClient, LLMError
from app.core.rate_limiter import RateLimiter, RateLimitStatus, global_rate_limiter
from app.models.chat import ChatLanguage, ChatRequest, ChatResponse
from app.repositories.chat_repository import ChatRepository

MAX_MESSAGE_LENGTH = 2000

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?88)?01[3-9]\d{8}|\b\d{8,15}\b")

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"```\s*system", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?rules", re.IGNORECASE),
]

SYSTEM_PROMPT_EN = (
    "You are PothSathi, a truthful bilingual travel assistant for Cox's Bazar, Bangladesh. "
    "Respond in the user's language (bn or en). Only answer questions about Cox's Bazar "
    "tourism, hotels, fares, beach safety, and emergencies. Never invent hotel names, "
    "phone numbers, or fares; cite only verified tool/seed data."
)

SYSTEM_PROMPT_BN = (
    "তুমি পথসাথী (PothSathi), কক্সবাজারের জন্য একটি সত্যনিষ্ঠ দ্বিভাষিক ভ্রমণ সহকারী। "
    "ব্যবহারকারী যে ভাষায় লেখে সেই ভাষায় উত্তর দাও। কখনো হোটেলের নাম, ফোন নম্বর বা ভাড়া "
    "বানিয়ে বলো না; শুধুমাত্র যাচাইকৃত তথ্যের উৎস উল্লেখ করে উত্তর দাও।"
)

AI_REST_MESSAGE_BN = "আমাদের AI সহকারী এখন বিশ্রামে আছে। নিচের তথ্যগুলো দেখুন।"
AI_REST_MESSAGE_EN = "Our AI assistant is resting. See the verified travel information below."


def detect_language(text: str, explicit_lang: ChatLanguage | None = None) -> ChatLanguage:
    """Detect Bengali vs English using Unicode block heuristic (\u0980-\u09FF)."""
    if explicit_lang in ("bn", "en"):
        return explicit_lang
    for ch in text:
        if "\u0980" <= ch <= "\u09ff":
            return "bn"
    return "en"


def strip_pii(text: str) -> str:
    """Strip email addresses and phone numbers before sending to Gemini (D6, D14)."""
    redacted = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_REGEX.sub("[REDACTED_PHONE]", redacted)
    return redacted


def check_prompt_injection(text: str) -> bool:
    """Return True if prompt injection patterns are detected (docs/ai-spec.md §10)."""
    return any(p.search(text) for p in INJECTION_PATTERNS)


class ChatService:
    """Orchestrates chat validation, PII stripping, rate limiting, and LLMClient calls."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        rate_limiter: RateLimiter | None = None,
        chat_repository: ChatRepository | None = None,
    ) -> None:
        self._llm = llm_client if llm_client is not None else LLMClient()
        self._limiter = rate_limiter if rate_limiter is not None else global_rate_limiter
        self._chat_repo = chat_repository

    async def process_message(
        self,
        payload: ChatRequest,
        uid: str | None = None,
        client_ip: str = "127.0.0.1",
    ) -> tuple[ChatResponse, RateLimitStatus]:
        raw_msg = payload.message.strip()
        if not raw_msg:
            raise InvalidInputError()
        if len(raw_msg) > MAX_MESSAGE_LENGTH:
            raise InputTooLongError()

        lang = detect_language(raw_msg, payload.language)

        # 1. Check user/IP rate limits
        rl_status = self._limiter.check_and_increment_user_or_ip(
            uid=uid,
            client_ip=client_ip,
        )

        # 2. Prompt injection guardrail
        if check_prompt_injection(raw_msg):
            refusal = (
                "আমি শুধু কক্সবাজার ভ্রমণের যাচাইকৃত তথ্য দিয়ে সাহায্য করতে পারি।"
                if lang == "bn"
                else "I can only assist with verified Cox's Bazar travel information."
            )
            return (
                ChatResponse(
                    answer_text=refusal,
                    language=lang,
                    session_id=payload.session_id,
                    severity="warning",
                ),
                rl_status,
            )

        # 3. Strip PII before sending to LLM or storing
        sanitized_msg = strip_pii(raw_msg)

        # 4. Global daily AI counter check ("AI rest mode" when exhausted)
        if not self._limiter.try_consume_global_ai_quota():
            rest_text = AI_REST_MESSAGE_BN if lang == "bn" else AI_REST_MESSAGE_EN
            return (
                ChatResponse(
                    answer_text=rest_text,
                    language=lang,
                    session_id=payload.session_id,
                    severity="warning",
                    fallback_used=True,
                    is_ai_resting=True,
                ),
                rl_status,
            )

        # 5. Call LLMClient wrapper
        sys_prompt = SYSTEM_PROMPT_BN if lang == "bn" else SYSTEM_PROMPT_EN
        try:
            llm_res = await self._llm.chat(
                messages=[{"role": "user", "content": sanitized_msg}],
                system_prompt=sys_prompt,
            )
            answer_text = llm_res.text or (
                AI_REST_MESSAGE_BN if lang == "bn" else AI_REST_MESSAGE_EN
            )
            fallback_used = False
            is_resting = False
        except LLMError:
            answer_text = AI_REST_MESSAGE_BN if lang == "bn" else AI_REST_MESSAGE_EN
            fallback_used = True
            is_resting = True

        # 6. Persist to chat_sessions if repository is wired and user is authenticated
        session_id = payload.session_id
        if self._chat_repo is not None and uid:
            try:
                session_doc = self._chat_repo.ensure_session(
                    uid=uid,
                    session_id=session_id,
                    language=lang,
                )
                session_id = session_doc.session_id
                self._chat_repo.save_message(session_id, "user", sanitized_msg, lang)
                self._chat_repo.save_message(session_id, "assistant", answer_text, lang)
            except Exception:
                # Non-fatal if emulator is not running during unit test
                pass

        return (
            ChatResponse(
                answer_text=answer_text,
                language=lang,
                session_id=session_id,
                fallback_used=fallback_used,
                is_ai_resting=is_resting,
            ),
            rl_status,
        )

    def get_sessions(self, uid: str, limit: int = 10, offset: int = 0) -> dict[str, Any]:
        repo = self._chat_repo if self._chat_repo is not None else ChatRepository()
        all_sessions = repo.list_sessions_for_user(uid)
        return {
            "items": all_sessions[offset : offset + limit],
            "total": len(all_sessions),
            "limit": limit,
            "offset": offset,
        }
