import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["dev", "test", "prod"] = "dev"
    FIREBASE_PROJECT_ID: str = "demo-pothsathi"
    FIRESTORE_EMULATOR_HOST: str | None = None
    FIREBASE_AUTH_EMULATOR_HOST: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    DAILY_AI_LIMIT: int = 500
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_environment_and_keys(self) -> "Settings":
        env = self.APP_ENV

        if env in ("dev", "test"):
            # In dev and test: emulator hosts default to localhost:8080 and localhost:9099
            if not self.FIRESTORE_EMULATOR_HOST:
                self.FIRESTORE_EMULATOR_HOST = "localhost:8080"
            if not self.FIREBASE_AUTH_EMULATOR_HOST:
                self.FIREBASE_AUTH_EMULATOR_HOST = "localhost:9099"

            # Set environment variables for google-cloud-firestore and firebase-admin SDKs
            os.environ["FIRESTORE_EMULATOR_HOST"] = self.FIRESTORE_EMULATOR_HOST
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = self.FIREBASE_AUTH_EMULATOR_HOST

        elif env == "prod":
            # In prod: refuse to start (clear error) if FIREBASE_PROJECT_ID,
            # credentials, GEMINI_API_KEY are missing OR if any emulator host variable is set (D19).
            if not self.FIREBASE_PROJECT_ID or self.FIREBASE_PROJECT_ID == "demo-pothsathi":
                raise ValueError(
                    "Production configuration error: FIREBASE_PROJECT_ID is required and "
                    "cannot be demo-pothsathi in production."
                )

            if not self.GOOGLE_APPLICATION_CREDENTIALS:
                raise ValueError(
                    "Production configuration error: "
                    "GOOGLE_APPLICATION_CREDENTIALS path is missing."
                )

            if not self.GEMINI_API_KEY:
                raise ValueError(
                    "Production configuration error: GEMINI_API_KEY is missing."
                )

            # Check if any emulator host variable is set in the model or in os.environ
            emulator_env = (
                self.FIRESTORE_EMULATOR_HOST
                or self.FIREBASE_AUTH_EMULATOR_HOST
                or os.environ.get("FIRESTORE_EMULATOR_HOST")
                or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
            )
            if emulator_env:
                raise ValueError(
                    "Production configuration error: Emulator host variables must NOT be set "
                    "in production (D19)."
                )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
