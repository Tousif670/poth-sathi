#!/usr/bin/env python3
"""Generate Tier 0 static JSON files in frontend/public/static/ from seed/ JSON files.

Per D10 and repo-structure.md:
- hotels.json -> frontend/public/static/hotels.json
- places.json -> frontend/public/static/places.json
- transport_routes.json -> frontend/public/static/fares.json
- beach_status.json -> frontend/public/static/beach_status.json
- emergency_contacts.json -> frontend/public/static/emergency.json
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "seed"
STATIC_OUT_DIR = REPO_ROOT / "frontend" / "public" / "static"

TIER0_MAPPINGS: list[tuple[str, str]] = [
    ("hotels.json", "hotels.json"),
    ("places.json", "places.json"),
    ("transport_routes.json", "fares.json"),
    ("beach_status.json", "beach_status.json"),
    ("emergency_contacts.json", "emergency.json"),
]


def build_tier0(seed_dir: Path = SEED_DIR, out_dir: Path = STATIC_OUT_DIR) -> dict[str, int]:
    """Read seed files and write static Tier 0 JSON files to frontend/public/static/."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for src_name, dst_name in TIER0_MAPPINGS:
        src_path = seed_dir / src_name
        if not src_path.exists():
            raise FileNotFoundError(f"Required seed file not found: {src_path}")

        data = json.loads(src_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Seed file {src_name} must contain a JSON array.")

        dst_path = out_dir / dst_name
        dst_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        counts[dst_name] = len(data)

    return counts


def main() -> None:
    try:
        counts = build_tier0()
    except Exception as exc:
        print(f"ERROR building Tier 0 static data: {exc}", file=sys.stderr)
        sys.exit(1)

    summary = ", ".join(f"{name}: {count}" for name, count in counts.items())
    print(f"Built Tier 0 static files in {STATIC_OUT_DIR} ({summary})")


if __name__ == "__main__":
    main()
