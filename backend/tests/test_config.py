import os

import pytest

from app.core.config import Settings


def test_dev_and_test_emulator_defaults():
    """In dev and test, emulator hosts default to localhost:8080 and localhost:9099."""
    settings_dev = Settings(
        APP_ENV="dev",
        FIRESTORE_EMULATOR_HOST=None,
        FIREBASE_AUTH_EMULATOR_HOST=None,
    )
    assert settings_dev.FIRESTORE_EMULATOR_HOST == "localhost:8080"
    assert settings_dev.FIREBASE_AUTH_EMULATOR_HOST == "localhost:9099"

    settings_test = Settings(
        APP_ENV="test",
        FIRESTORE_EMULATOR_HOST=None,
        FIREBASE_AUTH_EMULATOR_HOST=None,
    )
    assert settings_test.FIRESTORE_EMULATOR_HOST == "localhost:8080"
    assert settings_test.FIREBASE_AUTH_EMULATOR_HOST == "localhost:9099"


def test_prod_fails_without_keys():
    """In prod, refuse to start if project id, credentials, or gemini key are missing."""
    old_fs_emu = os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
    old_auth_emu = os.environ.pop("FIREBASE_AUTH_EMULATOR_HOST", None)

    try:
        # Missing all keys
        with pytest.raises(ValueError, match="Production configuration error"):
            Settings(
                APP_ENV="prod",
                FIREBASE_PROJECT_ID="",
                GOOGLE_APPLICATION_CREDENTIALS=None,
                GEMINI_API_KEY=None,
                FIRESTORE_EMULATOR_HOST=None,
                FIREBASE_AUTH_EMULATOR_HOST=None,
            )

        # Missing credentials
        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
            Settings(
                APP_ENV="prod",
                FIREBASE_PROJECT_ID="real-pothsathi-prod",
                GOOGLE_APPLICATION_CREDENTIALS=None,
                GEMINI_API_KEY="valid-gemini-key",
                FIRESTORE_EMULATOR_HOST=None,
                FIREBASE_AUTH_EMULATOR_HOST=None,
            )

        # Missing GEMINI_API_KEY
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            Settings(
                APP_ENV="prod",
                FIREBASE_PROJECT_ID="real-pothsathi-prod",
                GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json",
                GEMINI_API_KEY=None,
                FIRESTORE_EMULATOR_HOST=None,
                FIREBASE_AUTH_EMULATOR_HOST=None,
            )
    finally:
        if old_fs_emu:
            os.environ["FIRESTORE_EMULATOR_HOST"] = old_fs_emu
        if old_auth_emu:
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = old_auth_emu


def test_prod_fails_when_emulator_variable_set():
    """In prod, refuse to start if any emulator variable is set (D19)."""
    with pytest.raises(ValueError, match="Emulator host variables must NOT be set in production"):
        Settings(
            APP_ENV="prod",
            FIREBASE_PROJECT_ID="real-pothsathi-prod",
            GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json",
            GEMINI_API_KEY="valid-key",
            FIRESTORE_EMULATOR_HOST="localhost:8080",
            FIREBASE_AUTH_EMULATOR_HOST=None,
        )

    old_fs_emu = os.environ.get("FIRESTORE_EMULATOR_HOST")
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    try:
        with pytest.raises(ValueError, match="Emulator host variables must NOT be set"):
            Settings(
                APP_ENV="prod",
                FIREBASE_PROJECT_ID="real-pothsathi-prod",
                GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json",
                GEMINI_API_KEY="valid-key",
                FIRESTORE_EMULATOR_HOST=None,
                FIREBASE_AUTH_EMULATOR_HOST=None,
            )
    finally:
        if old_fs_emu:
            os.environ["FIRESTORE_EMULATOR_HOST"] = old_fs_emu
        else:
            os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
