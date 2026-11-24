#!/usr/bin/env python3
"""Loads verified seed data into Firestore (or Firestore Emulator).

Usage:
    python scripts/seed_loader.py [--allow-remote]
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add repo root and backend directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.core.firebase import get_firestore_client

from scripts.verify_seed import verify_all_seeds


def parse_args():
    parser = argparse.ArgumentParser(description="PothSathi Firestore Seed Loader")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow loading into remote Firestore (only permitted if APP_ENV != prod)",
    )
    return parser.parse_args()


def load_seeds(allow_remote: bool = False):
    # Step 1: Run verification first
    print("Running seed verification...")
    if not verify_all_seeds():
        print("Seed verification failed! Aborting load.", file=sys.stderr)
        sys.exit(1)

    settings = get_settings()

    # Step 2: Environment and emulator check
    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST") or settings.FIRESTORE_EMULATOR_HOST
    if settings.APP_ENV == "prod":
        print(
            "ERROR: Seed loader refuses to run in production environment (APP_ENV=prod)!",
            file=sys.stderr,
        )
        sys.exit(1)

    if not emulator_host and not allow_remote:
        print(
            "ERROR: FIRESTORE_EMULATOR_HOST is not set.\n"
            "To prevent accidental production writes, seed_loader requires the Firestore emulator.\n"
            "Start emulators with 'firebase emulators:start' or use '--allow-remote' in dev/test.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 3: Connect to Firestore
    db = get_firestore_client()
    seed_dir = repo_root / "seed"

    # Step 4: Load collections
    # 1. Hotels
    hotels_data = json.loads((seed_dir / "hotels.json").read_text(encoding="utf-8"))
    for hotel in hotels_data:
        doc_id = hotel.get("id") or hotel.get("hotel_id")
        db.collection("hotels").document(doc_id).set(hotel)
    hotel_count = len(hotels_data)

    # 2. Places
    places_data = json.loads((seed_dir / "places.json").read_text(encoding="utf-8"))
    for place in places_data:
        doc_id = place.get("id") or place.get("place_id")
        db.collection("places").document(doc_id).set(place)
    place_count = len(places_data)

    # 3. Transport Routes
    routes_data = json.loads((seed_dir / "transport_routes.json").read_text(encoding="utf-8"))
    for route in routes_data:
        doc_id = route.get("id") or route.get("route_id")
        db.collection("transport_routes").document(doc_id).set(route)
    route_count = len(routes_data)

    # 4. KB Chunks
    kb_data = json.loads((seed_dir / "kb_chunks.json").read_text(encoding="utf-8"))
    for chunk in kb_data:
        doc_id = chunk.get("id") or chunk.get("chunk_id")
        db.collection("kb_chunks").document(doc_id).set(chunk)
    kb_count = len(kb_data)

    # 5. Beach Status
    beach_data = json.loads((seed_dir / "beach_status.json").read_text(encoding="utf-8"))
    for zone in beach_data:
        doc_id = zone.get("zone_id") or zone.get("id")
        db.collection("beach_status").document(doc_id).set(zone)
    beach_count = len(beach_data)

    # Summary
    print(
        f"Loaded {hotel_count} hotels, {place_count} places, {route_count} routes, "
        f"{kb_count} kb_chunks, {beach_count} beach zones"
    )


if __name__ == "__main__":
    args = parse_args()
    load_seeds(allow_remote=args.allow_remote)
