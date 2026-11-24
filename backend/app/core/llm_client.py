from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import Settings, get_settings


class LLMError(Exception):
    """Base exception for LLMClient errors."""


class LLMQuotaError(LLMError):
    """Raised on HTTP 429 quota exhaustion."""


class LLMUnavailableError(LLMError):
    """Raised on HTTP 503 or missing API key in dev."""


class LLMTimeoutError(LLMError):
    """Raised when Gemini request times out."""


class LLMBadRequestError(LLMError):
    """Raised on HTTP 400 from Gemini."""


@dataclass
class LLMToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)


class LLMClient:
    """Single wrapper class around the Gemini API (D6, docs/ai-spec.md §2).
    Never receives user PII (name, email, phone).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings if settings is not None else get_settings()

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        api_key = self._settings.GEMINI_API_KEY
        if not api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not configured.")

        model_id = self._settings.GEMINI_MODEL or "gemini-1.5-flash"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_id}:generateContent?key={api_key}"
        )

        contents: list[dict[str, Any]] = []
        for msg in messages[-10:]:
            role = "model" if msg.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.2},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if tools:
            payload["tools"] = [{"functionDeclarations": tools}]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("Gemini request timed out.") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"Gemini network error: {exc}") from exc

        if resp.status_code == 429:
            raise LLMQuotaError("Gemini quota exhausted (429).")
        if resp.status_code >= 500:
            raise LLMUnavailableError(f"Gemini unavailable ({resp.status_code}).")
        if resp.status_code >= 400:
            raise LLMBadRequestError(f"Gemini bad request ({resp.status_code}).")

        body = resp.json()
        candidates = body.get("candidates") or []
        if not candidates:
            return LLMResponse(text="")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        text_chunks: list[str] = []
        tool_calls: list[LLMToolCall] = []

        for part in parts:
            if "text" in part and isinstance(part["text"], str):
                text_chunks.append(part["text"])
            if "functionCall" in part and isinstance(part["functionCall"], dict):
                fc = part["functionCall"]
                tool_calls.append(
                    LLMToolCall(
                        name=str(fc.get("name", "")),
                        args=dict(fc.get("args") or {}),
                    )
                )

        return LLMResponse(text="\n".join(text_chunks).strip(), tool_calls=tool_calls)

    async def embed(self, text: str) -> list[float]:
        api_key = self._settings.GEMINI_API_KEY
        if not api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not configured.")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"text-embedding-004:embedContent?key={api_key}"
        )
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text[:2000]}]},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("Gemini embedding timed out.") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError("Gemini embedding failed.") from exc

        if resp.status_code == 429:
            raise LLMQuotaError("Gemini embedding quota exhausted.")
        if resp.status_code >= 400:
            raise LLMUnavailableError(f"Gemini embedding error ({resp.status_code}).")

        values = (resp.json().get("embedding") or {}).get("values")
        if not isinstance(values, list):
            raise LLMUnavailableError("Invalid embedding response.")
        return [float(v) for v in values]


class FakeLLMClient(LLMClient):
    """Deterministic FakeLLMClient for unit/integration tests (docs/ai-spec.md §2)."""

    def __init__(
        self,
        canned_text: str = "EXAMPLE grounded response from FakeLLMClient.",
        canned_tool_calls: list[LLMToolCall] | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        super().__init__(settings=get_settings())
        self.canned_text = canned_text
        self.canned_tool_calls = canned_tool_calls or []
        self.raise_error = raise_error
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {"messages": messages, "tools": tools, "system_prompt": system_prompt}
        )
        if self.raise_error is not None:
            raise self.raise_error
        # On second round-trip after tool execution, return final text without looping tool calls
        if len(self.calls) > 1:
            return LLMResponse(text=self.canned_text, tool_calls=[])
        return LLMResponse(text=self.canned_text, tool_calls=list(self.canned_tool_calls))

    async def embed(self, text: str) -> list[float]:
        if self.raise_error is not None:
            raise self.raise_error
        return [0.1, 0.2, 0.3, 0.4]
