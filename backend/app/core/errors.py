from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application exception following api-spec conventions."""

    def __init__(
        self,
        code: str,
        message_bn: str,
        message_en: str,
        http_status: int = 400,
    ):
        super().__init__(message_en)
        self.code = code
        self.message_bn = message_bn
        self.message_en = message_en
        self.http_status = http_status

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message_bn": self.message_bn,
                "message_en": self.message_en,
            }
        }


class NotFoundError(AppError):
    def __init__(
        self,
        message_bn: str = "অনুরোধ করা তথ্য পাওয়া যায়নি।",
        message_en: str = "Requested resource was not found.",
        code: str = "NOT_FOUND",
    ):
        super().__init__(code=code, message_bn=message_bn, message_en=message_en, http_status=404)


class DatabaseUnavailableError(AppError):
    def __init__(
        self,
        message_bn: str = "ডাটাবেজ সাময়িকভাবে অনুপলব্ধ। অনুগ্রহ করে কিছুক্ষণ পর চেষ্টা করুন।",
        message_en: str = "Database service is temporarily unavailable.",
        code: str = "DB_UNAVAILABLE",
    ):
        super().__init__(code=code, message_bn=message_bn, message_en=message_en, http_status=503)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content=exc.to_dict())


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message_bn": "অনুরোধের তথ্য সঠিক নয়।",
                "message_en": "Invalid request payload or query parameters.",
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = f"HTTP_{exc.status_code}"
    msg_en = str(exc.detail) if exc.detail else "An HTTP error occurred."
    msg_bn = (
        "অনুরোধ করা পৃষ্ঠা বা তথ্য পাওয়া যায়নি।"
        if exc.status_code == 404
        else "অনুরোধ প্রক্রিয়া করতে সমস্যা হয়েছে।"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message_bn": msg_bn,
                "message_en": msg_en,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never expose internal traceback or PII to the client
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message_bn": "একটি অপ্রত্যাশিত ত্রুটি ঘটেছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
                "message_en": "An unexpected server error occurred. Please try again later.",
            }
        },
    )
