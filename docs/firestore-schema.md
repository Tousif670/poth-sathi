# PothSathi — Firestore Schema

> Binding decisions: [decisions.md](decisions.md).
> Architecture: [architecture.md](architecture.md).
> AI tools and RAG: [ai-spec.md](ai-spec.md).

---

## 1  Principles

- **Public reference data vs per-user data.** Reference collections (hotels, places, transport_routes, kb_chunks, beach_status) are public read-through-API. Per-user collections (users, chat_sessions, usage, sos_events, reports) are scoped to one uid.
- **Only FastAPI writes.** The frontend never touches Firestore directly. Security rules deny all client access. The backend uses a service-account key.
- **Bilingual fields.** Every human-readable text field is a map: `{ "bn": "...", "en": "..." }`.
- **Geohash.** Every place/hotel with coordinates stores a `geohash` string (6 chars) for future geospatial queries. At MVP scale (≤40 docs) brute-force haversine is used instead (see architecture.md §8).
- **Metadata triple.** Every reference record carries `data_source` (string), `is_verified` (bool), `last_updated` (timestamp).

---

## 2  Collections Overview

| # | Collection | Purpose | Writer | Reader | Priority |
| --- | --- | --- | --- | --- | --- |
| 1 | `users/{uid}` | User profile and role | FastAPI (on first login) | FastAPI (auth check) | P0 |
| 2 | `hotels/{hotel_id}` | Verified hotel reference data | Seed loader / Admin API | FastAPI (cached) | P0 |
| 3 | `hotels/{hotel_id}/reviews/{review_id}` | User-submitted hotel reviews | FastAPI (chat / review endpoint) | FastAPI | P1 |
| 4 | `places/{place_id}` | Nearby essentials (hospital, ATM…) | Seed loader / Admin API | FastAPI (cached) | P0 |
| 5 | `transport_routes/{route_id}` | Fare routes with price ranges | Seed loader / Admin API | FastAPI (cached) | P0 |
| 6 | `kb_chunks/{chunk_id}` | Knowledge-base text + embedding | Seed loader / Admin API | FastAPI (startup load) | P0 |
| 7 | `beach_status/{zone_id}` | Beach safety flag per zone | Admin API | FastAPI (cached, 2 min TTL) | P0 |
| 8 | `sos_events/{id}` | SOS button presses with location | FastAPI (SOS endpoint) | Admin API | P0 |
| 9 | `chat_sessions/{session_id}/messages/{message_id}` | Chat history (30-day expiry) | FastAPI (after each turn) | FastAPI (last 10 msgs) | P0 |
| 10 | `usage/{uid_date}` | Per-user daily chat counter | FastAPI (increment) | FastAPI (rate limit check) | P0 |
| 11 | `ai_usage/{date}` | Global daily AI call counter | FastAPI (increment) | FastAPI (rate limit check) | P0 |
| 12 | `reports/{id}` | "Report wrong info" submissions | FastAPI (report endpoint) | Admin API | P1 |
| 13 | `admin_audit/{id}` | Log of admin actions | FastAPI (admin endpoints) | Admin API (read-only) | P1 |

---

## 3  Collection Details

### 3.1  `users/{uid}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `uid` | string | ✓ | Firebase Auth uid (= doc id) |
| `role` | string | ✓ | `"tourist"` or `"admin"` — set manually for admin |
| `display_name` | string | | From Firebase Auth or user input |
| `auth_provider` | string | ✓ | `"anonymous"`, `"google"`, `"email"` |
| `preferred_language` | string | | `"bn"` or `"en"`, default `"bn"` |
| `created_at` | timestamp | ✓ | |
| `last_login` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "uid": "EXAMPLE_UID_abc123",
  "role": "tourist",
  "display_name": "EXAMPLE_USER",
  "auth_provider": "google",
  "preferred_language": "bn",
  "created_at": "2026-11-25T10:00:00Z",
  "last_login": "2026-11-25T10:00:00Z"
}
```

**Indexes:** None beyond default (queries by `uid` only).

---

### 3.2  `hotels/{hotel_id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `hotel_id` | string | ✓ | Auto-generated or slug (= doc id) |
| `name` | map `{bn, en}` | ✓ | Bilingual hotel name |
| `area` | string | ✓ | `"kolatoli"`, `"sugandha"`, or `"laboni"` |
| `description` | map `{bn, en}` | | Short description |
| `price_min_bdt` | number | ✓ | Min nightly rate in BDT |
| `price_max_bdt` | number | ✓ | Max nightly rate in BDT |
| `amenities` | array\<string\> | ✓ | e.g. `["wifi", "pool", "restaurant"]` |
| `rating` | number | | 0.0–5.0 (seed rating or average of reviews) |
| `address` | map `{bn, en}` | | |
| `phone` | string | | Contact number |
| `lat` | number | ✓ | Latitude |
| `lon` | number | ✓ | Longitude |
| `geohash` | string | ✓ | 6-char geohash of lat/lon |
| `image_url` | string | | URL to hotel photo (own photo only) |
| `data_source` | string | ✓ | e.g. `"field_visit"`, `"hotel_website"` |
| `is_verified` | bool | ✓ | `true` if manually verified |
| `last_updated` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "hotel_id": "EXAMPLE_hotel_001",
  "name": { "bn": "EXAMPLE_হোটেল_নাম", "en": "EXAMPLE_Hotel_Name" },
  "area": "kolatoli",
  "description": { "bn": "EXAMPLE_বর্ণনা", "en": "EXAMPLE_description" },
  "price_min_bdt": 0,
  "price_max_bdt": 0,
  "amenities": ["wifi", "restaurant"],
  "rating": 0.0,
  "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
  "phone": "EXAMPLE_PHONE",
  "lat": 21.4272,
  "lon": 91.9710,
  "geohash": "EXMPL1",
  "image_url": "",
  "data_source": "field_visit",
  "is_verified": false,
  "last_updated": "2026-11-25T00:00:00Z"
}
```

**Indexes:**
- Composite: `area` ASC + `price_max_bdt` ASC (hotel search with area + price filter).
- Composite: `area` ASC + `rating` DESC (hotel search sorted by rating).

---

### 3.3  `hotels/{hotel_id}/reviews/{review_id}`

Priority: **P1**.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `review_id` | string | ✓ | Auto-generated (= doc id) |
| `uid` | string | ✓ | Author's Firebase uid |
| `text` | string | ✓ | Review text (≤500 chars) |
| `language` | string | ✓ | `"bn"` or `"en"` |
| `rating` | number | ✓ | 1–5 |
| `sentiment` | string | | `"positive"`, `"negative"`, `"neutral"` — set by backend |
| `sentiment_aspects` | map | | Aspect scores from sentiment analyzer |
| `created_at` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "review_id": "EXAMPLE_rev_001",
  "uid": "EXAMPLE_UID_abc123",
  "text": "EXAMPLE_review_text",
  "language": "en",
  "rating": 4,
  "sentiment": "positive",
  "sentiment_aspects": { "Food": "positive", "Cleanliness": "neutral" },
  "created_at": "2026-11-26T14:00:00Z"
}
```

**Indexes:**
- Composite: `hotels/{hotel_id}/reviews` → `created_at` DESC (recent reviews first).

---

### 3.4  `places/{place_id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `place_id` | string | ✓ | Auto-generated or slug (= doc id) |
| `name` | map `{bn, en}` | ✓ | |
| `category` | string | ✓ | `"hospital"`, `"pharmacy"`, `"atm"`, `"mosque"`, `"police"` |
| `description` | map `{bn, en}` | | |
| `address` | map `{bn, en}` | | |
| `phone` | string | | |
| `opening_hours` | string | | e.g. `"24/7"` or `"08:00–22:00"` |
| `lat` | number | ✓ | |
| `lon` | number | ✓ | |
| `geohash` | string | ✓ | 6-char |
| `data_source` | string | ✓ | |
| `is_verified` | bool | ✓ | |
| `last_updated` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "place_id": "EXAMPLE_place_001",
  "name": { "bn": "EXAMPLE_হাসপাতাল", "en": "EXAMPLE_Hospital" },
  "category": "hospital",
  "description": { "bn": "EXAMPLE_বর্ণনা", "en": "EXAMPLE_description" },
  "address": { "bn": "EXAMPLE_ঠিকানা", "en": "EXAMPLE_address" },
  "phone": "EXAMPLE_PHONE",
  "opening_hours": "24/7",
  "lat": 21.4350,
  "lon": 91.9680,
  "geohash": "EXMPL2",
  "data_source": "openstreetmap",
  "is_verified": false,
  "last_updated": "2026-11-25T00:00:00Z"
}
```

**Indexes:**
- Single-field: `category` ASC (filter by category).

---

### 3.5  `transport_routes/{route_id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `route_id` | string | ✓ | Auto-generated (= doc id) |
| `origin` | map `{bn, en}` | ✓ | Starting location name |
| `destination` | map `{bn, en}` | ✓ | Destination name |
| `vehicle_type` | string | ✓ | `"cng_auto"`, `"rickshaw"`, `"bus"`, `"tomtom"` |
| `fare_basis` | string | ✓ | `"per_vehicle"` or `"per_person"` (D22) |
| `fare_min_bdt` | number | ✓ | Min fare in BDT |
| `fare_max_bdt` | number | ✓ | Max fare in BDT |
| `distance_km` | number | | Approximate distance |
| `notes` | map `{bn, en}` | | e.g. "shared fare" vs "reserved" |
| `data_source` | string | ✓ | |
| `is_verified` | bool | ✓ | |
| `last_updated` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "route_id": "EXAMPLE_route_001",
  "origin": { "bn": "EXAMPLE_উৎপত্তি", "en": "EXAMPLE_Origin" },
  "destination": { "bn": "EXAMPLE_গন্তব্য", "en": "EXAMPLE_Destination" },
  "vehicle_type": "cng_auto",
  "fare_basis": "per_vehicle",
  "fare_min_bdt": 0,
  "fare_max_bdt": 0,
  "distance_km": 0,
  "notes": { "bn": "EXAMPLE_নোট", "en": "EXAMPLE_note" },
  "data_source": "field_visit",
  "is_verified": false,
  "last_updated": "2026-11-25T00:00:00Z"
}
```

Per D22, each route has `fare_basis` (`per_vehicle` or `per_person`), `vehicle_type`, `fare_min_bdt`, `fare_max_bdt`. `calculate_fare` and `GET /api/v1/transport/calculate` take origin, destination, optional mode, optional passengers; passengers multiplies the fare only when `fare_basis` is `per_person`.

**Indexes:**
- Composite: `origin.en` ASC + `destination.en` ASC (route lookup by text).

---

### 3.6  `kb_chunks/{chunk_id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `chunk_id` | string | ✓ | Auto-generated (= doc id) |
| `text` | map `{bn, en}` | ✓ | 100–300 words, hand-curated |
| `category` | string | ✓ | e.g. `"beach_safety"`, `"food_guide"`, `"cultural_tips"`, `"transport_advice"`, `"emergency"`, `"general"` |
| `source` | string | ✓ | e.g. `"own_writing"`, `"official_notice"` |
| `embedding` | array\<number\> | ✓ | 3072-dim float vector, pre-computed |
| `language` | string | ✓ | `"both"`, `"bn"`, or `"en"` |
| `data_source` | string | ✓ | Same as `source` (for consistency) |
| `is_verified` | bool | ✓ | |
| `last_updated` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "chunk_id": "EXAMPLE_kb_001",
  "text": {
    "bn": "EXAMPLE_বাংলা_টেক্সট — কক্সবাজার সমুদ্র সৈকতে সাঁতার কাটার সময় সতর্ক থাকুন।",
    "en": "EXAMPLE_English_text — Stay alert while swimming at Cox's Bazar beach."
  },
  "category": "beach_safety",
  "source": "own_writing",
  "embedding": [0.012, -0.034, 0.056],
  "language": "both",
  "data_source": "own_writing",
  "is_verified": true,
  "last_updated": "2026-11-25T00:00:00Z"
}
```

**Indexes:** None beyond default (all chunks loaded at startup for in-memory index).

---

### 3.7  `beach_status/{zone_id}`

Multi-zone collection per D23: `beach_status/{zone_id}` with zone_ids `kolatoli`, `sugandha`, `laboni` (seed file `beach_status.json` has 3 zones).

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `zone_id` | string | ✓ | `"kolatoli"`, `"sugandha"`, or `"laboni"` (= doc id) |
| `zone_name` | map `{bn, en}` | ✓ | |
| `flag_colour` | string | ✓ | `"green"`, `"yellow"`, or `"red"` |
| `note` | map `{bn, en}` | | Safety note from admin |
| `set_by` | string | ✓ | Admin uid who set it |
| `last_updated` | timestamp | ✓ | |
| `data_source` | string | ✓ | `"admin_manual"` |
| `is_verified` | bool | ✓ | Always `true` (admin-set) |

**EXAMPLE document:**

```json
{
  "zone_id": "kolatoli",
  "zone_name": { "bn": "কলাতলী সৈকত", "en": "Kolatoli Beach" },
  "flag_colour": "yellow",
  "note": { "bn": "EXAMPLE_সতর্কতা", "en": "EXAMPLE_caution" },
  "set_by": "EXAMPLE_ADMIN_UID",
  "last_updated": "2026-11-25T08:00:00Z",
  "data_source": "admin_manual",
  "is_verified": true
}
```

**Indexes:** None (single-document lookup by zone_id).

---

### 3.8  `sos_events/{id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | ✓ | Auto-generated (= doc id) |
| `uid` | string | ✓ | User who triggered SOS |
| `lat` | number | | User latitude (if granted) |
| `lon` | number | | User longitude (if granted) |
| `message` | string | | Optional short description |
| `status` | string | ✓ | `"active"`, `"resolved"` |
| `created_at` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "id": "EXAMPLE_sos_001",
  "uid": "EXAMPLE_UID_abc123",
  "lat": 21.4300,
  "lon": 91.9700,
  "message": "",
  "status": "active",
  "created_at": "2026-11-25T15:30:00Z"
}
```

**Indexes:** None (admin queries by `created_at` DESC — single-field auto-index).

---

### 3.9  `chat_sessions/{session_id}/messages/{message_id}`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `session_id` | string | ✓ | = uid (one session per user for MVP) |
| `message_id` | string | ✓ | Auto-generated (= doc id) |
| `role` | string | ✓ | `"user"` or `"assistant"` |
| `text` | string | ✓ | Message content |
| `language` | string | ✓ | `"bn"` or `"en"` |
| `tool_calls_used` | array\<string\> | | Tools used in this response |
| `fallback_used` | bool | | |
| `safety_triggered` | bool | | |
| `created_at` | timestamp | ✓ | |
| `expires_at` | timestamp | ✓ | `created_at + 30 days` — for cleanup |

The parent doc `chat_sessions/{session_id}` stores:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `session_id` | string | ✓ | = uid |
| `uid` | string | ✓ | |
| `created_at` | timestamp | ✓ | |
| `last_message_at` | timestamp | ✓ | Updated on each message |
| `message_count` | number | ✓ | Incremented per message |

**EXAMPLE (parent):**

```json
{
  "session_id": "EXAMPLE_UID_abc123",
  "uid": "EXAMPLE_UID_abc123",
  "created_at": "2026-11-25T10:00:00Z",
  "last_message_at": "2026-11-25T10:05:00Z",
  "message_count": 4
}
```

**EXAMPLE (message):**

```json
{
  "message_id": "EXAMPLE_msg_001",
  "role": "user",
  "text": "EXAMPLE_message_text",
  "language": "bn",
  "tool_calls_used": [],
  "fallback_used": false,
  "safety_triggered": false,
  "created_at": "2026-11-25T10:05:00Z",
  "expires_at": "2026-12-25T10:05:00Z"
}
```

**Indexes:**
- Composite: `chat_sessions/{session_id}/messages` → `created_at` DESC (fetch last 10).

---

### 3.10  `usage/{uid_date}`

Doc id format: `{uid}_{YYYY-MM-DD}`. Resets by calendar date YYYY-MM-DD in Asia/Dhaka time (UTC+6) per D26.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `uid` | string | ✓ | |
| `date` | string | ✓ | `"YYYY-MM-DD"` in Asia/Dhaka time (UTC+6; D26) |
| `chat_count` | number | ✓ | Incremented per chat message; limit 50/day (D15) |
| `last_chat_at` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "uid": "EXAMPLE_UID_abc123",
  "date": "2026-11-25",
  "chat_count": 12,
  "last_chat_at": "2026-11-25T16:30:00Z"
}
```

**Indexes:** None (direct doc lookup by id).

---

### 3.11  `ai_usage/{date}`

Doc id: `YYYY-MM-DD`. One doc per day, global counter. Resets by calendar date YYYY-MM-DD in Asia/Dhaka time (UTC+6) per D26.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | string | ✓ | `"YYYY-MM-DD"` in Asia/Dhaka time (UTC+6; D26) |
| `call_count` | number | ✓ | Incremented per Gemini API call |
| `embedding_count` | number | ✓ | Incremented per embedding call |
| `limit` | number | ✓ | From env `DAILY_AI_LIMIT` |
| `is_exhausted` | bool | ✓ | `true` when `call_count >= limit` |

**EXAMPLE document:**

```json
{
  "date": "2026-11-25",
  "call_count": 142,
  "embedding_count": 85,
  "limit": 500,
  "is_exhausted": false
}
```

**Indexes:** None (direct doc lookup by date).

---

### 3.12  `reports/{id}`

Priority: **P1**.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | ✓ | Auto-generated (= doc id) |
| `uid` | string | ✓ | Reporter's uid |
| `target_collection` | string | ✓ | e.g. `"hotels"`, `"places"`, `"transport_routes"` |
| `target_id` | string | ✓ | Doc id of the reported record |
| `reason` | string | ✓ | Free text (≤500 chars) |
| `status` | string | ✓ | `"pending"`, `"reviewed"`, `"fixed"`, `"dismissed"` |
| `created_at` | timestamp | ✓ | |
| `reviewed_at` | timestamp | | |
| `reviewed_by` | string | | Admin uid |

**EXAMPLE document:**

```json
{
  "id": "EXAMPLE_report_001",
  "uid": "EXAMPLE_UID_abc123",
  "target_collection": "hotels",
  "target_id": "EXAMPLE_hotel_001",
  "reason": "EXAMPLE_reason_text",
  "status": "pending",
  "created_at": "2026-11-26T09:00:00Z"
}
```

**Indexes:**
- Single-field: `status` ASC (admin queries pending reports).

---

### 3.13  `admin_audit/{id}`

Priority: **P1**.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | ✓ | Auto-generated (= doc id) |
| `admin_uid` | string | ✓ | Who performed the action |
| `action` | string | ✓ | e.g. `"update_hotel"`, `"set_beach_flag"`, `"resolve_report"` |
| `target_collection` | string | ✓ | |
| `target_id` | string | ✓ | |
| `changes` | map | | Before/after summary (no PII) |
| `created_at` | timestamp | ✓ | |

**EXAMPLE document:**

```json
{
  "id": "EXAMPLE_audit_001",
  "admin_uid": "EXAMPLE_ADMIN_UID",
  "action": "set_beach_flag",
  "target_collection": "beach_status",
  "target_id": "main",
  "changes": { "flag_colour": { "before": "green", "after": "yellow" } },
  "created_at": "2026-11-25T08:00:00Z"
}
```

**Indexes:** None (admin reads by `created_at` DESC — single-field auto-index).

---

## 4  Required Composite Indexes

Firestore auto-creates single-field indexes. These composite indexes must be created manually (or via `firebase.json` / `firestore.indexes.json`):

| # | Collection | Fields | Purpose |
| --- | --- | --- | --- |
| 1 | `hotels` | `area` ASC, `price_max_bdt` ASC | Hotel search: area + price filter |
| 2 | `hotels` | `area` ASC, `rating` DESC | Hotel search: area + sort by rating |
| 3 | `hotels/{id}/reviews` | `created_at` DESC | Recent reviews for a hotel |
| 4 | `chat_sessions/{id}/messages` | `created_at` DESC | Last 10 messages |

---

## 5  Access Patterns per Screen

| Screen | Collection(s) read | Query | Reads per visit | Cached? |
| --- | --- | --- | --- | --- |
| **Home** | `beach_status` | 3 docs (`kolatoli`, `sugandha`, `laboni`) | 3 | Yes, 2 min TTL |
| **Hotels list** | `hotels` | All docs (≤25) | 25 | Yes, 10 min TTL |
| **Hotel detail** | `hotels`, `reviews` (P1) | 1 hotel + last 10 reviews | 11 | Hotel cached; reviews not cached |
| **Nearby map** | `places` | All docs by category (≤40) | 40 | Yes, 10 min TTL |
| **Fares** | `transport_routes` | All docs (≤15) | 15 | Yes, 30 min TTL |
| **Beach safety** | `beach_status` | 3 docs | 3 | Yes, 2 min TTL |
| **Emergency / SOS** | None (Tier 0 static) | — | 0 | N/A |
| **Chat (per msg)** | `usage`, `ai_usage`, `chat_sessions/messages`, `kb_chunks` | Counter check + last 10 msgs | 13 | kb_chunks cached at startup; usage not cached |
| **Admin panel** (P1) | `hotels`, `places`, `reports`, `admin_audit` | Various | ≤50 | Not cached |
| **Login** | `users` | 1 doc (upsert) | 1 | Not cached |

---

## 6  Estimated Daily Reads/Writes vs Spark Limits

**Assumptions:** 30 active users/day, each visits 5 screens, sends 10 chat messages.

### Reads (without caching)

| Action | Reads per user | × 30 users | Daily total |
| --- | --- | --- | --- |
| Home (beach_status) | 1 | 30 | 30 |
| Hotels list | 25 | 750 | 750 |
| Hotel detail (1 visit) | 11 | 330 | 330 |
| Nearby map | 40 | 1 200 | 1 200 |
| Fares | 15 | 450 | 450 |
| Beach safety | 1 | 30 | 30 |
| Login (user doc) | 1 | 30 | 30 |
| Chat (10 msgs × 13 reads) | 130 | 3 900 | 3 900 |
| **Total without cache** | | | **6 720** |

### Effect of caching

The backend TTL cache means that within a TTL window, only the first request triggers Firestore reads. With 30 users over a day:

| Collection | TTL | Estimated cache-hit rate | Reads saved |
| --- | --- | --- | --- |
| `hotels` | 10 min | ~90% | 750 → 75 |
| `places` | 10 min | ~90% | 1 200 → 120 |
| `transport_routes` | 30 min | ~95% | 450 → 23 |
| `beach_status` | 2 min | ~70% | 60 → 18 |
| `kb_chunks` | Startup | ~99% | 0 (loaded once) |

**Reads with caching:** ~75 + 120 + 23 + 18 + 30 + 330 + 3 900 ≈ **4 500 reads/day**.

### Tier 0 static data effect

Emergency and Fares pages can serve from Tier 0 static JSON (built at deploy time). If 50% of fare/emergency visits use Tier 0 → saves another ~200 reads.

**Final estimate: ~4 300 reads/day** vs **50 000 Spark limit** → **8.6% of quota**. Safe.

### Writes

| Action | Writes per user | × 30 users | Daily total |
| --- | --- | --- | --- |
| Login (user upsert) | 1 | 30 | 30 |
| Chat messages (10 user + 10 assistant) | 20 | 600 | 600 |
| Chat session update (10 msgs) | 10 | 300 | 300 |
| Usage counter (10 increments) | 10 | 300 | 300 |
| AI usage counter (10 increments) | 1 (batched) | 30 | 30 |
| **Total writes** | | | **1 260** |

**1 260 writes/day** vs **20 000 Spark limit** → **6.3% of quota**. Safe.

### Scaling note

At **100 users/day** (without caching changes), estimated reads would be ~15 000 (30% of quota). Still safe but should monitor in Firebase console.

---

## 7  Security Rules

### Approach

All client access is **denied**. Only the FastAPI backend (using `google-cloud-firestore` with a service-account key) reads and writes Firestore. Firebase Auth is a separate product and is called directly by the frontend.

### Rules file: `firestore.rules`

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Deny ALL client reads and writes.
    // All access goes through the FastAPI backend
    // using a service-account key (admin SDK).
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### Why deny-all is correct here

- D4: "The frontend talks only to FastAPI (login excepted). Firestore client access is denied by security rules."
- The backend uses `firebase-admin` Python SDK, which bypasses security rules entirely (admin access).
- No client-side Firestore SDK is included in the frontend.

---

## 8  Retention and Cleanup

| Data | Retention | Cleanup method |
| --- | --- | --- |
| Chat messages | 30 days (D14) | Scheduled cleanup script or Cloud Function (Later). For MVP: manual delete via admin. `expires_at` field marks eligible docs. |
| Usage counters | 90 days | Manual cleanup. Old counters are small and harmless. |
| AI usage counters | 90 days | Manual cleanup. |
| SOS events | Indefinite | Admin can resolve and archive. |
| Reports | Indefinite | Admin reviews and resolves. |
| Admin audit | Indefinite | Read-only log. |
| Reference data (hotels, places, routes, KB, beach) | Indefinite | Updated via seed loader or admin. |

### MVP cleanup approach

No automated cleanup in MVP (would need Cloud Functions or a cron job, adding complexity). The `expires_at` field on chat messages marks them for future cleanup. A script in `scripts/cleanup_expired_chats.py` can be run manually.

---

## 9  Seed File Mapping

Each seed file maps to one Firestore collection. The seed loader script (`scripts/seed_loader.py`) reads these files and writes to Firestore (or the emulator).

| Seed file | Collection | Format | Notes |
| --- | --- | --- | --- |
| `seed/hotels.json` | `hotels` | Array of hotel objects | See §3.2 for fields |
| `seed/places.json` | `places` | Array of place objects | See §3.4 for fields |
| `seed/transport_routes.json` | `transport_routes` | Array of route objects | See §3.5 for fields |
| `seed/kb_chunks.json` | `kb_chunks` | Array of chunk objects | Embeddings added by `scripts/compute_embeddings.py` |
| `seed/beach_status.json` | `beach_status` | Array of 3 zone objects | Initial flags for kolatoli, sugandha, laboni (D23) |
| `seed/emergency_contacts.json` | — (Tier 0 only) | Array | Built into frontend static, not stored in Firestore |
| `seed/safety_rules.json` | — (backend code) | JSON | Loaded by safety rule engine at startup |

---

## Open Questions

1. **Chat session per user vs per visit:** This schema uses `session_id = uid` (one session per user). Should there be multiple sessions per user? decisions.md says "30 days" but not whether sessions reset. Assumed one rolling session for MVP.
2. **Subcollection vs top-level for reviews:** This schema uses `hotels/{hotel_id}/reviews/{review_id}` (subcollection). An alternative is a top-level `reviews` collection with a `hotel_id` field. Subcollection is simpler for "get reviews for hotel X" queries but harder for "get all reviews by user Y". Assumed subcollection since the primary query is per-hotel.
3. **Transport route index on bilingual map fields:** Firestore cannot index nested map fields like `origin.en` for equality queries. The `calculate_fare` tool uses fuzzy matching in Python after loading all routes from cache. If this changes, the schema may need flat `origin_en`, `origin_bn` fields.
4. **kb_chunks embedding storage:** Storing 3072-dim float arrays as Firestore arrays is valid but reads the entire array on every doc read. At ≤300 chunks loaded once at startup, this is acceptable. For larger datasets, consider storing embeddings in a separate file.

---

*End of firestore-schema. ~300 lines.*
