#!/usr/bin/env python3
"""Validates all seed JSON files against Pydantic schemas.

Exits with code 0 on success, or code 1 on any schema validation error.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path

# Add repo root and backend directory to sys.path so app models can be imported
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.hotel import HotelDoc
from app.models.kb import KBChunkDoc
from app.models.place import PlaceDoc
from app.models.safety import (
    BeachStatusDoc,
    EmergencyContactDoc,
    SafetyRulesDoc,
)
from app.models.transport import RouteDoc


def verify_file(name: str, loader_fn: Callable[[], int | str]) -> bool:
    try:
        count = loader_fn()
        label = f"{count} records valid" if isinstance(count, int) else f"{count} valid"
        print(f"✓ seed/{name}: {label}")
        return True
    except (AssertionError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"✗ seed/{name}: FAILED - {e}", file=sys.stderr)
        return False


def verify_all_seeds() -> bool:
    seed_dir = repo_root / "seed"
    all_ok = True

    # 1. hotels.json
    def check_hotels() -> int:
        path = seed_dir / "hotels.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 3, f"Expected at least 3 hotels, found {len(data)}"
        for item in data:
            HotelDoc(**item)
        return len(data)

    all_ok &= verify_file("hotels.json", check_hotels)

    # 2. places.json
    def check_places() -> int:
        path = seed_dir / "places.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 6, f"Expected at least 6 places, found {len(data)}"
        categories = {item.get("category") for item in data}
        required_cats = {"hospital", "pharmacy", "police", "atm"}
        assert required_cats.issubset(
            categories
        ), f"Missing categories: {required_cats - categories}"
        for item in data:
            PlaceDoc(**item)
        return len(data)

    all_ok &= verify_file("places.json", check_places)

    # 3. transport_routes.json
    def check_routes() -> int:
        path = seed_dir / "transport_routes.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 3, f"Expected at least 3 routes, found {len(data)}"
        bases = {item.get("fare_basis") for item in data}
        assert "per_vehicle" in bases and "per_person" in bases, (
            "Must include both per_vehicle and per_person routes"
        )
        for item in data:
            RouteDoc(**item)
        return len(data)

    all_ok &= verify_file("transport_routes.json", check_routes)

    # 4. kb_chunks.json
    def check_kb() -> int:
        path = seed_dir / "kb_chunks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 4, f"Expected at least 4 chunks, found {len(data)}"
        for item in data:
            KBChunkDoc(**item)
        return len(data)

    all_ok &= verify_file("kb_chunks.json", check_kb)

    # 5. beach_status.json
    def check_beach() -> str:
        path = seed_dir / "beach_status.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        zones = {item.get("zone_id") for item in data}
        assert {"kolatoli", "sugandha", "laboni"}.issubset(zones), f"Missing zones: {zones}"
        for item in data:
            BeachStatusDoc(**item)
        return f"{len(data)} zones"

    all_ok &= verify_file("beach_status.json", check_beach)

    # 6. emergency_contacts.json
    def check_emergency() -> int:
        path = seed_dir / "emergency_contacts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            doc = EmergencyContactDoc(**item)
            if doc.number != "999":
                assert doc.number == "TO_VERIFY", f"Number must be TO_VERIFY, got {doc.number}"
            assert doc.status == "TO_VERIFY", f"Status must be TO_VERIFY, got {doc.status}"
        return len(data)

    all_ok &= verify_file("emergency_contacts.json", check_emergency)

    # 7. safety_rules.json
    def check_safety_rules() -> str:
        path = seed_dir / "safety_rules.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        rules_doc = SafetyRulesDoc(**data)
        for rule in rules_doc.rules:
            assert len(rule.keywords_bn) >= 3, f"Need >=3 bn keywords in {rule.category}"
            assert len(rule.keywords_en) >= 3, f"Need >=3 en keywords in {rule.category}"
            assert len(rule.keywords_banglish) >= 3, (
                f"Need >=3 banglish keywords in {rule.category}"
            )
            assert rule.status == "REVIEW"
        return f"{len(rules_doc.rules)} rules"

    all_ok &= verify_file("safety_rules.json", check_safety_rules)

    return all_ok


if __name__ == "__main__":
    if not verify_all_seeds():
        sys.exit(1)
