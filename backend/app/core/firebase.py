import os
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.client import Client

from app.core.config import Settings, get_settings
from app.core.logging import logger

_db_client: Client | None = None


def initialize_firebase(settings: Settings | None = None) -> Client:
    """Initializes Firebase Admin SDK and returns a Firestore client.

    In dev and test, it connects to the local emulator and will refuse to run if
    the emulator host is not configured, ensuring it never touches production.
    """
    global _db_client
    if _db_client is not None:
        return _db_client

    if settings is None:
        settings = get_settings()

    if settings.APP_ENV in ("dev", "test"):
        if not settings.FIRESTORE_EMULATOR_HOST:
            raise RuntimeError(
                f"Safety check failed: FIRESTORE_EMULATOR_HOST must be set in {settings.APP_ENV}."
            )
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
        if settings.FIREBASE_AUTH_EMULATOR_HOST:
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.FIREBASE_AUTH_EMULATOR_HOST

        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})

        _db_client = firestore.Client(
            project=settings.FIREBASE_PROJECT_ID,
            credentials=AnonymousCredentials(),
        )
        logger.info(
            f"Initialized Firebase Admin ({settings.APP_ENV}) emulator: "
            f"{settings.FIRESTORE_EMULATOR_HOST}"
        )
    else:
        # Production mode
        if not settings.GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        ):
            raise RuntimeError(
                f"Production credentials file not found: {settings.GOOGLE_APPLICATION_CREDENTIALS}"
            )
        cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                cred, options={"projectId": settings.FIREBASE_PROJECT_ID}
            )
        _db_client = firestore.client()
        logger.info("Initialized Firebase Admin in production with service account credentials.")

    return _db_client


def get_firestore_client() -> Client:
    """Get the active Firestore client, initializing if necessary."""
    global _db_client
    if _db_client is None:
        return initialize_firebase()
    return _db_client


def check_firestore_connection(timeout_seconds: float = 2.0) -> bool:
    """Check if Firestore connection is healthy without throwing exceptions."""
    try:
        client = get_firestore_client()
        docs: Any = client.collection("beach_status").limit(1).get(timeout=timeout_seconds)
        _ = list(docs)
        return True
    except Exception as e:
        logger.warning(f"Firestore health check failed: {e}")
        return False
