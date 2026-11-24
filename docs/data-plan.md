# PothSathi — Data Plan

> Binding decisions: [decisions.md](decisions.md).
> Schema details: [firestore-schema.md](firestore-schema.md).

---

## 1  Data Inventory

| # | Dataset | Collection | Key fields | Possible sources | Who verifies | Demo target (D9) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Hotels | `hotels` | name, area, price range, amenities, coordinates | Hotel websites, Google Maps (coordinates only), field visits | Developer (manual) | 15–25 |
| 2 | Nearby places | `places` | name, category, coordinates, hours | OpenStreetMap (with attribution), field visits, Google Maps (coordinates only) | Developer (manual) | 30–40 |
| 3 | Transport routes | `transport_routes` | origin, destination, vehicle type, fare range | Field visits, local inquiry, official CNG union notices (if available) | Developer (manual) | 10–15 |
| 4 | KB chunks | `kb_chunks` | text (bn+en), category, embedding | Own writing, official Cox's Bazar notices, travel guides (rewritten, not copied) | Developer | 40–60 |
| 5 | Beach status | `beach_status` | flag colour, note, set_by | Admin manual entry based on local observation | Admin (developer) | 3 zones (kolatoli, sugandha, laboni) |
| 6 | Emergency contacts | Tier 0 static | service name, number | Government websites, official directories — **all numbers TO VERIFY** | Developer (manual) | 5–8 entries |
| 7 | Safety rules | Backend JSON | keywords (bn, en, Banglish), response keys | Developer-curated + native Bengali speaker review | Developer | 6 categories |

---

## 2  Verification Workflow

### Statuses

| Status | Meaning | UI display |
| --- | --- | --- |
| `draft` | Data entered but not checked | Hidden from public (admin-only) |
| `verified` | Manually confirmed by developer | Normal display |
| `sample` | Placeholder for demo, not real | Shows **"sample / indicative"** badge |
| `outdated` | Was verified but `last_updated` > 90 days | Shows **"may be outdated"** badge |

### Status mapping to schema fields

- `is_verified: true` → `verified`
- `is_verified: false` + `data_source: "sample"` → `sample`
- `is_verified: false` + `data_source` ≠ `"sample"` → `draft`
- `is_verified: true` + `last_updated` older than 90 days → `outdated` (checked at read time)

### Stale-data policy

- Reference data older than **90 days** is flagged `outdated` at read time (not written back).
- Beach status older than **6 hours** shows "may be outdated" (see ai-spec.md §5.4).
- The admin page (P1) shows a list of records sorted by `last_updated` ascending to highlight stale data.
- No auto-deletion of stale data — it stays until admin updates or removes it.

---

## 3  Seed File Templates

All files live in `seed/`. Format: JSON arrays. All names, numbers, and prices below are **EXAMPLE placeholders** — replace with real verified data.

### 3.1  `seed/hotels.json`

```json
[
  {
    "hotel_id": "EXAMPLE_hotel_001",
    "name": { "bn": "EXAMPLE_হোটেল_ক", "en": "EXAMPLE_Hotel_A" },
    "area": "kolatoli",
    "description": { "bn": "EXAMPLE_বর্ণনা_ক", "en": "EXAMPLE_description_A" },
    "price_min_bdt": 0,
    "price_max_bdt": 0,
    "amenities": ["wifi", "restaurant"],
    "rating": 0.0,
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "EXAMPLE_PHONE",
    "lat": 21.4272,
    "lon": 91.9710,
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "hotel_id": "EXAMPLE_hotel_002",
    "name": { "bn": "EXAMPLE_হোটেল_খ", "en": "EXAMPLE_Hotel_B" },
    "area": "sugandha",
    "description": { "bn": "EXAMPLE_বর্ণনা_খ", "en": "EXAMPLE_description_B" },
    "price_min_bdt": 0,
    "price_max_bdt": 0,
    "amenities": ["wifi", "pool", "parking"],
    "rating": 0.0,
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "EXAMPLE_PHONE",
    "lat": 21.4320,
    "lon": 91.9690,
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "hotel_id": "EXAMPLE_hotel_003",
    "name": { "bn": "EXAMPLE_হোটেল_গ", "en": "EXAMPLE_Hotel_C" },
    "area": "laboni",
    "description": { "bn": "EXAMPLE_বর্ণনা_গ", "en": "EXAMPLE_description_C" },
    "price_min_bdt": 0,
    "price_max_bdt": 0,
    "amenities": ["wifi"],
    "rating": 0.0,
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "EXAMPLE_PHONE",
    "lat": 21.4380,
    "lon": 91.9720,
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  }
]
```

### 3.2  `seed/places.json`

```json
[
  {
    "place_id": "EXAMPLE_place_001",
    "name": { "bn": "EXAMPLE_হাসপাতাল_ক", "en": "EXAMPLE_Hospital_A" },
    "category": "hospital",
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "EXAMPLE_PHONE",
    "opening_hours": "24/7",
    "lat": 21.4350,
    "lon": 91.9680,
    "data_source": "openstreetmap",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "place_id": "EXAMPLE_place_002",
    "name": { "bn": "EXAMPLE_ফার্মেসি_ক", "en": "EXAMPLE_Pharmacy_A" },
    "category": "pharmacy",
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "EXAMPLE_PHONE",
    "opening_hours": "08:00–23:00",
    "lat": 21.4290,
    "lon": 91.9705,
    "data_source": "field_visit",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "place_id": "EXAMPLE_place_003",
    "name": { "bn": "EXAMPLE_এটিএম_ক", "en": "EXAMPLE_ATM_A" },
    "category": "atm",
    "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
    "phone": "",
    "opening_hours": "24/7",
    "lat": 21.4310,
    "lon": 91.9695,
    "data_source": "openstreetmap",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  }
]
```

### 3.3  `seed/transport_routes.json`

```json
[
  {
    "route_id": "EXAMPLE_route_001",
    "origin": { "bn": "EXAMPLE_উৎপত্তি_ক", "en": "EXAMPLE_Origin_A" },
    "destination": { "bn": "EXAMPLE_গন্তব্য_ক", "en": "EXAMPLE_Destination_A" },
    "vehicle_type": "cng_auto",
    "fare_basis": "per_vehicle",
    "fare_min_bdt": 0,
    "fare_max_bdt": 0,
    "distance_km": 0,
    "notes": { "bn": "", "en": "" },
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "route_id": "EXAMPLE_route_002",
    "origin": { "bn": "EXAMPLE_উৎপত্তি_খ", "en": "EXAMPLE_Origin_B" },
    "destination": { "bn": "EXAMPLE_গন্তব্য_খ", "en": "EXAMPLE_Destination_B" },
    "vehicle_type": "rickshaw",
    "fare_basis": "per_vehicle",
    "fare_min_bdt": 0,
    "fare_max_bdt": 0,
    "distance_km": 0,
    "notes": { "bn": "", "en": "" },
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  },
  {
    "route_id": "EXAMPLE_route_003",
    "origin": { "bn": "EXAMPLE_উৎপত্তি_গ", "en": "EXAMPLE_Origin_C" },
    "destination": { "bn": "EXAMPLE_গন্তব্য_গ", "en": "EXAMPLE_Destination_C" },
    "vehicle_type": "bus",
    "fare_basis": "per_person",
    "fare_min_bdt": 0,
    "fare_max_bdt": 0,
    "distance_km": 0,
    "notes": { "bn": "", "en": "" },
    "data_source": "EXAMPLE_SOURCE",
    "is_verified": false,
    "last_updated": "2026-11-25T00:00:00Z"
  }
]
```

### 3.4  `seed/kb_chunks.json`

```json
[
  {
    "chunk_id": "EXAMPLE_kb_001",
    "text": { "bn": "EXAMPLE_বাংলা_টেক্সট", "en": "EXAMPLE_English_text" },
    "category": "beach_safety",
    "source": "own_writing",
    "language": "both",
    "data_source": "own_writing",
    "is_verified": true,
    "last_updated": "2026-11-25T00:00:00Z"
  }
]
```

> Embeddings are **not** in the seed file. Run `scripts/compute_embeddings.py` to add them before seeding Firestore.

### 3.5  `seed/emergency_contacts.json`

```json
[
  { "service": { "bn": "জাতীয় জরুরি সেবা", "en": "National Emergency" }, "number": "999", "status": "TO_VERIFY" },
  { "service": { "bn": "ফায়ার সার্ভিস", "en": "Fire Service" }, "number": "199", "status": "TO_VERIFY" },
  { "service": { "bn": "নারী ও শিশু হেল্পলাইন", "en": "Women & Children Helpline" }, "number": "10921", "status": "TO_VERIFY" }
]
```

---

## 4  Knowledge-Base Chunk Format

Each chunk is 100–300 words of **hand-curated text** (D7). Never auto-split from large documents.

### Structure

```json
{
  "chunk_id": "beach_safety_rip_current",
  "text": {
    "bn": "কক্সবাজার সমুদ্র সৈকতে রিপ কারেন্ট একটি গুরুতর বিপদ। ... [EXAMPLE — 100-300 words of curated Bengali text about rip current safety. Source: developer's own writing based on PLACEHOLDER_SOURCE. Do not copy from any website.]",
    "en": "Rip currents are a serious danger at Cox's Bazar beach. ... [EXAMPLE — 100-300 words of curated English text about rip current safety. Source: developer's own writing based on PLACEHOLDER_SOURCE. Do not copy from any website.]"
  },
  "category": "beach_safety",
  "source": "own_writing — based on PLACEHOLDER_SOURCE (verify)",
  "language": "both",
  "data_source": "own_writing",
  "is_verified": true,
  "last_updated": "2026-11-25T00:00:00Z"
}
```

### Category list

| Category | Topic examples | Target chunks |
| --- | --- | --- |
| `beach_safety` | Rip currents, swimming rules, flag meanings, tides | 8–10 |
| `food_guide` | Local dishes, restaurant areas, food safety tips | 6–8 |
| `cultural_tips` | Local customs, dress code, prayer times, festivals | 5–7 |
| `transport_advice` | CNG fare negotiation, bus from Dhaka, local transport | 5–7 |
| `emergency` | What to do in emergency, hospital access, police | 4–5 |
| `general` | Weather, best season, travel tips, packing, currency | 8–12 |
| **Total** | | **40–60** |

### Writing guidelines

1. Write in simple, clear language. Avoid jargon.
2. Each chunk covers **one specific topic** (e.g., "Rip current safety", not "Beach safety overview").
3. Bengali and English versions must convey the same information.
4. Cite your source in the `source` field. If based on personal knowledge, write `"own_writing"`.
5. Never copy text from hotel websites, travel blogs, or any copyrighted source. Rewrite in your own words.
6. Mark any unverifiable fact with `(verify)` in the text.

---

## 5  Beach Flag Update Process

1. **Admin opens** the admin panel → Beach Status section.
2. **Admin selects** the zone (`kolatoli`, `sugandha`, or `laboni`) and flag colour: green (safe), yellow (caution), red (danger).
3. **Admin writes** an optional bilingual note (e.g., "Strong currents expected this afternoon").
4. **Backend** writes to `beach_status/{zone_id}` with `set_by: admin_uid`, `last_updated: now()`.
5. **Backend** writes to `admin_audit` collection for the audit trail.
6. **Backend** clears the beach_status TTL cache (2 min), so the next request gets the fresh flag.
7. **Frontend** displays the new flag immediately on refresh; the `last_updated` timestamp is always shown.
8. **If `last_updated` > 6 hours:** the UI and the `get_beach_status` tool add `"may be outdated"` to the display (see ai-spec.md §5.4).

> **MVP note:** There is no external data feed for beach flags. The admin sets the flag manually based on local observation. Seed file `seed/beach_status.json` seeds all 3 zones (`kolatoli`, `sugandha`, `laboni`) per D23. Open-Meteo wave data is supplementary information only, not an automatic trigger.

---

## 6  Legal and Attribution Notes

| Concern | Rule |
| --- | --- |
| **OpenStreetMap** | All map tiles display `"© OpenStreetMap contributors"` as required by the ODbL licence. Place coordinates sourced from OSM are marked `data_source: "openstreetmap"`. See tile usage policy: wiki.openstreetmap.org/wiki/Tile_usage_policy — verify. |
| **Hotel descriptions** | All descriptions are written by the developer in their own words. Never copy text from hotel websites, Booking.com, TripAdvisor, or any third party. |
| **Hotel photos** | Only use own photos or photos with explicit permission. No downloaded images from hotel websites or booking platforms. For MVP, use placeholder images or no images. |
| **Emergency numbers** | Sourced from government directories. All marked **TO VERIFY** until confirmed. |
| **Gemini free-tier data use** | Free-tier prompts may be used by Google (D6). The UI shows a privacy notice. No PII is sent to Gemini (D14). |
| **Personal data** | No personal data is stored beyond Firebase Auth profile (uid, email, display name). Chat text is kept 30 days max (D14). GPS coordinates are used only for SOS events, never logged (D14). |
| **KB chunk sources** | Each chunk cites its source. If based on official notices, cite the notice. If original writing, mark `"own_writing"`. Never plagiarise. |
| **Font licences** | Hind Siliguri: OFL licence. Noto Sans Bengali: OFL licence. Both free for use. |

---

## 7  Data Collection Checklist

Today is **23 November 2026**. Feature freeze is **4 December 2026**. This checklist aligns with D17.

| Day | Date | Task | Target |
| --- | --- | --- | --- |
| 1 | Nov 23 (Sat) | Set up seed file templates with EXAMPLE data. Write 5 KB chunks (beach_safety). | 5 chunks, templates ready |
| 2 | Nov 24 (Sun) | Collect hotel data: list 15 hotels with names, areas, coordinates from public sources. Mark all `sample`. | 15 hotel drafts |
| 3 | Nov 25 (Mon) | Collect place data: list 20 places (hospitals, pharmacies, ATMs, mosques, police) from OSM. Mark `sample`. | 20 place drafts |
| 4 | Nov 26 (Tue) | Collect transport routes: list 10 routes with vehicle types. Mark `sample`. Write 5 more KB chunks (food_guide, cultural_tips). | 10 routes, 10 chunks |
| 5 | Nov 27 (Wed) | Write 10 more KB chunks (transport_advice, emergency, general). Fill emergency contacts. | 20 chunks, emergency data |
| 6 | Nov 28 (Thu) | Write 10 more KB chunks. Add 10 more places (total 30). Verify 5 hotels (upgrade to `verified`). | 30 chunks, 30 places |
| 7 | Nov 29 (Fri) | Write remaining KB chunks (target 40). Add remaining hotels (total 20). Run `compute_embeddings.py`. | 40 chunks, 20 hotels |
| 8 | Nov 30 (Sat) | Verify all transport routes. Verify 10 more hotels. Run seed loader against emulator. Fix data issues. | Seed tested in emulator |
| 9 | Dec 1 (Sun) | Add 5 more KB chunks (target 45). Add remaining places (target 35). Second embedding run. | 45 chunks, 35 places |
| 10 | Dec 2 (Mon) | Final data review: check all `is_verified` flags, `last_updated` dates, bilingual text completeness. | Data review complete |
| 11 | Dec 3 (Tue) | Seed production Firestore. Verify beach_status and emergency contacts. Write 5 buffer KB chunks. | 50 chunks, production seeded |
| 12 | Dec 4 (Wed) | **Feature freeze.** Final data check. Fix any reported data issues. No new data after this. | Data frozen |

> **If behind schedule:** Prioritise hotels (15 minimum), places (20 minimum), routes (10 minimum), and KB chunks (30 minimum). These are the floors for a credible demo.

---

## Open Questions

1. **Hotel data sourcing without field visits:** If travel to Cox's Bazar is not possible before the deadline, all hotel data will be `sample` status. Is that acceptable for the demo? The UI will show "sample / indicative" badges.
2. **OpenStreetMap data quality for Cox's Bazar:** OSM coverage for smaller roads and businesses in Cox's Bazar may be incomplete. The developer should check Overpass Turbo for category coverage before relying on OSM as the primary place source.
3. **Bengali keyboard for KB chunks:** Writing 40–60 bilingual chunks requires a Bengali keyboard or input method. Plan time for this.

---

*End of data-plan. ~150 lines.*
