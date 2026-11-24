import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.auth import router as auth_router
from app.api.v1.emergency import router as emergency_router
from app.api.v1.health import router as health_router
from app.api.v1.hotels import router as hotels_router
from app.api.v1.nearby import router as nearby_router
from app.api.v1.safety import router as safety_router
from app.api.v1.transport import router as transport_router
from app.core.config import Settings, get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.firebase import initialize_firebase
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(f"Starting PothSathi backend [APP_ENV={settings.APP_ENV}]")
    try:
        initialize_firebase(settings)
    except Exception as e:
        logger.warning(f"Initial Firebase setup warning: {e}")
    yield
    logger.info("Shutting down PothSathi backend.")


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="PothSathi API",
        version="0.1.0",
        description="Bilingual AI Tourism Companion for Cox's Bazar",
        lifespan=lifespan,
    )

    # CORS configuration from env
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Structured request logging middleware (never logs bodies or PII per D14)
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
        )
        return response

    # Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth_router, prefix="/api/v1", tags=["Auth & Profile"])
    app.include_router(hotels_router, prefix="/api/v1", tags=["Hotels"])
    app.include_router(nearby_router, prefix="/api/v1", tags=["Nearby Essentials"])
    app.include_router(transport_router, prefix="/api/v1", tags=["Transport & Fares"])
    app.include_router(safety_router, prefix="/api/v1", tags=["Safety & Advisories"])
    app.include_router(emergency_router, prefix="/api/v1", tags=["Emergency & SOS"])

    return app


app = create_app()
