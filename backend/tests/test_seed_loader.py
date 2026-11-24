from pathlib import Path

import pytest
from scripts.seed_loader import load_seeds

from app.core.firebase import check_firestore_connection, get_firestore_client

repo_root = Path(__file__).resolve().parent.parent.parent


def test_seed_loader_and_idempotency():
    """Loads into emulator, asserts collection counts, and verifies idempotency."""
    if not check_firestore_connection(timeout_seconds=1.0):
        pytest.skip("Firestore emulator is not running at localhost:8080")

    db = get_firestore_client()

    # First load
    load_seeds(allow_remote=False)

    hotels_count = len(list(db.collection("hotels").stream()))
    places_count = len(list(db.collection("places").stream()))
    routes_count = len(list(db.collection("transport_routes").stream()))
    kb_count = len(list(db.collection("kb_chunks").stream()))
    beach_count = len(list(db.collection("beach_status").stream()))

    assert hotels_count == 3, f"Expected 3 hotels, got {hotels_count}"
    assert places_count == 6, f"Expected 6 places, got {places_count}"
    assert routes_count == 3, f"Expected 3 routes, got {routes_count}"
    assert kb_count == 4, f"Expected 4 kb_chunks, got {kb_count}"
    assert beach_count == 3, f"Expected 3 beach zones, got {beach_count}"

    # Second load: must be idempotent and counts must not change
    load_seeds(allow_remote=False)

    assert len(list(db.collection("hotels").stream())) == 3
    assert len(list(db.collection("places").stream())) == 6
    assert len(list(db.collection("transport_routes").stream())) == 3
    assert len(list(db.collection("kb_chunks").stream())) == 4
    assert len(list(db.collection("beach_status").stream())) == 3
