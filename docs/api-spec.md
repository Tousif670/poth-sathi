# PothSathi — REST API Specification

> Binding decisions: [decisions.md](decisions.md).  
> Architecture: [architecture.md](architecture.md).  
> AI tools and pipeline: [ai-spec.md](ai-spec.md).  
> Firestore schema: [firestore-schema.md](firestore-schema.md).

---

## 1 Conventions & Architecture Rules

### 1.1 Base Path & Protocol
- **Base URL:** `/api/v1` (versioned prefix).
- **Transport:** HTTPS mandatory in production; plain HTTP permitted on `localhost` for testing.
- **Content-Type:** `application/json` for all request and response payloads.

### 1.2 Authentication & Guest Handling
- **Header:** `Authorization: Bearer <firebase_id_token>`.
- **Tourists & Guests:** Tourists authenticate via Firebase Auth (Google OAuth, email/password, or Firebase Anonymous Auth). Anonymous users receive a valid Firebase ID token and are stored in Firestore `users/{uid}` with `role: "tourist"` and `auth_provider: "anonymous"`.
- **Unauthenticated Fallback:** Public endpoints (`GET /hotels`, `GET /nearby`, `GET /transport/fares`, `GET /safety/*`, `GET /emergency/contacts`) allow requests without an `Authorization` header. These are rate-limited by client IP.
- **Admin Access:** Endpoints prefixed with `/api/v1/admin` require a verified Firebase ID token where the Firestore `users/{uid}` record has `role == "admin"`. Otherwise, return `403 Forbidden`.

### 1.3 Localization
- **Parameter:** `lang` query parameter (`bn` or `en`). Defaults to `bn`.
- Alternatively, the `Accept-Language` header is respected if `lang` is omitted.
- Multilingual Firestore documents (`{ "bn": "...", "en": "..." }`) are resolved to the requested language string by the backend before serialization, or returned as full localized maps on detailed resources.

### 1.4 Standard Error Response Format
All 4xx and 5xx responses use a single unified JSON structure:
```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message_bn": "বাংলা ভাষায় ব্যবহারকারী বান্ধব বার্তা।",
    "message_en": "User-facing error message in English."
  }
}
```

### 1.5 Pagination & Query Conventions
- **Offset-based pagination:** `limit` (integer, default `10`, max `50`) and `offset` (integer, default `0`).
- **Paginated Response Envelope:**
  ```json
  {
    "items": [ ... ],
    "total": 42,
    "limit": 10,
    "offset": 0
  }
  ```

### 1.6 Rate Limiting & Headers
Limits are tracked in-memory by the backend (D15):
- Authenticated tourists: 50 chat messages / 24 hours.
- Guests / Public IP: 100 requests / 1 hour.
- Global AI safety cap: daily token/cost circuit breaker ("AI rest mode").

**Rate-limit response headers:**
- `X-RateLimit-Limit`: Maximum permitted calls in current window.
- `X-RateLimit-Remaining`: Remaining calls permitted before lockout.
- `X-RateLimit-Reset`: Unix epoch timestamp when counter resets.

### 1.7 HTTP Status Codes
| Code | Meaning | Usage |
| --- | --- | --- |
| `200 OK` | Success | Successful GET, PATCH, or synchronous calculation |
| `201 Created` | Resource Created | Successful POST creation |
| `204 No Content` | Success (No Body) | Successful DELETE |
| `400 Bad Request` | Invalid Input | Validation failed, missing required fields |
| `401 Unauthorized` | Auth Required | Missing, expired, or invalid Firebase ID token |
| `403 Forbidden` | Access Denied | Authenticated tourist attempting admin action |
| `404 Not Found` | Not Found | Resource ID does not exist |
| `429 Too Many Requests` | Rate Limited | User or IP quota exceeded |
| `500 Internal Error` | Server Failure | Unexpected backend error |
| `503 Service Unavailable` | Downstream Outage | Firestore or Gemini unavailable |

---

## 2 Module 1: Auth and Profile

Manages user registration, session sync, profile retrieval, preference updates, and account deletion.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `POST /api/v1/auth/register` | Authenticated (Any) | Body: `{ "display_name": string?, "preferred_language": "bn" or "en"? }` | `201 Created`<br>`UserProfile` | `400 INVALID_INPUT`<br>`401 INVALID_TOKEN` | `users/{uid}` |
| `GET /api/v1/me` | Authenticated (Any) | None | `200 OK`<br>`UserProfile` | `401 INVALID_TOKEN`<br>`404 USER_NOT_FOUND` | `users/{uid}` |
| `PATCH /api/v1/me` | Authenticated (Any) | Body: `{ "display_name"?: string, "preferred_language"?: "bn" or "en" }` | `200 OK`<br>`UserProfile` | `400 INVALID_INPUT`<br>`401 INVALID_TOKEN` | `users/{uid}` |
| `DELETE /api/v1/me` | Authenticated (Any) | None | `204 No Content` | `401 INVALID_TOKEN`<br>`404 USER_NOT_FOUND` | `users/{uid}`, `usage/{uid_date}` |

### Key Endpoint Example: `POST /api/v1/auth/register`
**Request:**
```http
POST /api/v1/auth/register HTTP/1.1
Host: api.pothsathi.example
Authorization: Bearer EXAMPLE_FIREBASE_ID_TOKEN
Content-Type: application/json

{
  "display_name": "EXAMPLE_Tourist",
  "preferred_language": "bn"
}
```

**Response (`201 Created`):**
```json
{
  "uid": "EXAMPLE_UID_abc123",
  "role": "tourist",
  "display_name": "EXAMPLE_Tourist",
  "auth_provider": "google",
  "preferred_language": "bn",
  "created_at": "2026-11-25T10:00:00Z",
  "last_login": "2026-11-25T10:00:00Z"
}
```

---

## 3 Module 2: Hotels

Browse verified hotels with recommendation match scores, area filters, budget caps, and detail inspection.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/hotels` | Public / Guest | Query: `area` ("kolatoli", "sugandha", or "laboni"), `max_price_bdt` (number), `amenities` (comma-separated), `sort` ("match", "price_asc", "price_desc", "rating"), `lang`, `limit`, `offset` | `200 OK`<br>`PaginatedList<HotelListItem>` | `400 INVALID_QUERY_PARAM` | `hotels/{hotel_id}` |
| `GET /api/v1/hotels/{id}` | Public / Guest | Path: `id` (string)<br>Query: `lang` | `200 OK`<br>`HotelDetail` | `404 HOTEL_NOT_FOUND` | `hotels/{hotel_id}` |

### Key Endpoint Example: `GET /api/v1/hotels`
**Request:**
```http
GET /api/v1/hotels?area=kolatoli&max_price_bdt=3000&amenities=wifi,pool&sort=match&lang=en&limit=1 HTTP/1.1
Host: api.pothsathi.example
```

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "hotel_id": "EXAMPLE_hotel_001",
      "name": "EXAMPLE_Sea_View",
      "area": "kolatoli",
      "price_min_bdt": 2500,
      "price_max_bdt": 4500,
      "amenities": ["wifi", "pool", "restaurant"],
      "rating": 4.2,
      "lat": 21.4167,
      "lon": 91.9833,
      "is_verified": true,
      "data_source": "field_visit",
      "last_updated": "2026-11-20T12:00:00Z",
      "match_score": 0.918
    }
  ],
  "total": 1,
  "limit": 1,
  "offset": 0
}
```

---

## 4 Module 3: Reviews (P1)

Community reviews with lightweight rule-based sentiment analysis upon submission.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/hotels/{id}/reviews` | Public / Guest | Path: `id` (string)<br>Query: `limit`, `offset` | `200 OK`<br>`PaginatedList<ReviewItem>` | `404 HOTEL_NOT_FOUND` | `hotels/{hotel_id}/reviews/{review_id}` |
| `POST /api/v1/hotels/{id}/reviews` | Authenticated Tourist | Path: `id` (string)<br>Body: `{ "rating": number, "comment": string, "lang"?: "bn" or "en" }` | `201 Created`<br>`ReviewWithSentiment` | `400 INVALID_INPUT`<br>`401 INVALID_TOKEN`<br>`404 HOTEL_NOT_FOUND` | `hotels/{hotel_id}/reviews/{review_id}`, `hotels/{hotel_id}` |

### Key Endpoint Example: `POST /api/v1/hotels/{id}/reviews`
**Request:**
```http
POST /api/v1/hotels/EXAMPLE_hotel_001/reviews HTTP/1.1
Host: api.pothsathi.example
Authorization: Bearer EXAMPLE_FIREBASE_ID_TOKEN
Content-Type: application/json

{
  "rating": 4,
  "comment": "Room was clean and service was friendly, but breakfast was delayed.",
  "lang": "en"
}
```

**Response (`201 Created`):**
```json
{
  "review_id": "EXAMPLE_rev_987",
  "hotel_id": "EXAMPLE_hotel_001",
  "uid": "EXAMPLE_UID_abc123",
  "rating": 4,
  "comment": "Room was clean and service was friendly, but breakfast was delayed.",
  "created_at": "2026-11-25T14:30:00Z",
  "sentiment": {
    "overall": "positive",
    "confidence": 0.72,
    "aspects": {
      "Food": { "sentiment": "neutral", "positive": 0, "negative": 0 },
      "Cleanliness": { "sentiment": "positive", "positive": 1, "negative": 0 },
      "Location": { "sentiment": "neutral", "positive": 0, "negative": 0 },
      "Service": { "sentiment": "positive", "positive": 1, "negative": 0 },
      "Price": { "sentiment": "neutral", "positive": 0, "negative": 0 }
    }
  }
}
```

---

## 5 Module 4: Nearby Essentials

Locates nearby places (hospitals, pharmacies, police, ATMs, mosques) within a given geographic radius.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/nearby` | Public / Guest | Query: `category` ("hospital", "pharmacy", "police", "atm", "mosque", or "all"), `lat` (number), `lng` (number), `radius_km` (number, default 2.0), `lang`, `limit` | `200 OK`<br>`NearbyResponse` | `400 INVALID_COORDINATES` | `places/{place_id}` |

### Key Endpoint Example: `GET /api/v1/nearby`
**Request:**
```http
GET /api/v1/nearby?category=pharmacy&lat=21.4167&lng=91.9833&radius_km=1.5&lang=bn HTTP/1.1
Host: api.pothsathi.example
```

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "place_id": "EXAMPLE_place_pharmacy_01",
      "name": "EXAMPLE_সৈকত_ফার্মেসি",
      "category": "pharmacy",
      "address": "EXAMPLE_কলাতলী_মেইন_রোড",
      "lat": 21.4170,
      "lon": 91.9840,
      "distance_km": 0.08,
      "phone": "EXAMPLE_01700000000",
      "is_verified": true,
      "data_source": "field_visit",
      "last_updated": "2026-11-20T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

## 6 Module 5: Transport & Fares

Fetches verified local transport routes and calculates estimated fare ranges across vehicle modes.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/transport/fares` | Public / Guest | Query: `origin` (string?), `destination` (string?), `mode` ("tomtom", "cng", "rickshaw", or "chander_gari"?), `lang` | `200 OK`<br>`FareRouteList` | `400 INVALID_QUERY_PARAM` | `transport_routes/{route_id}` |
| `GET /api/v1/transport/calculate` | Public / Guest | Query: `origin` (string), `destination` (string), `mode` ("tomtom", "cng", "rickshaw", or "chander_gari"?), `passengers` (integer, default 1), `lang` | `200 OK`<br>`FareCalculationResponse` | `400 ROUTE_NOT_FOUND` | `transport_routes/{route_id}` |

### Key Endpoint Example: `GET /api/v1/transport/calculate`
**Request:**
```http
GET /api/v1/transport/calculate?origin=kolatoli&destination=laboni&mode=tomtom&passengers=2&lang=en HTTP/1.1
Host: api.pothsathi.example
```

**Response (`200 OK`):**
```json
{
  "origin": "kolatoli",
  "destination": "laboni",
  "mode": "tomtom",
  "passengers": 2,
  "fare_basis": "per_person",
  "min_fare_bdt": 40,
  "max_fare_bdt": 60,
  "estimated_time_min": 15,
  "distance_km": 3.5,
  "route_id": "EXAMPLE_route_001",
  "is_verified": true,
  "data_source": "local_government_rates",
  "last_updated": "2026-11-20T10:00:00Z",
  "notes": "Standard daytime fare per person. Passengers multiplies fare only when fare_basis is per_person (D22)."
}
```


---

## 7 Module 6: Safety and Advisories

Provides current beach hazard flags and regional tourist safety advisories.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/safety/beach-status` | Public / Guest | Query: `zone_id` ("kolatoli", "sugandha", or "laboni"? Optional; if omitted, returns all three zones), `lang` | `200 OK`<br>`BeachStatusResponse` | None | `beach_status/{zone_id}` |
| `GET /api/v1/safety/advisories` | Public / Guest | Query: `lang` | `200 OK`<br>`AdvisoriesResponse` | None | `kb_chunks/{chunk_id}` |

### Key Endpoint Example: `GET /api/v1/safety/beach-status`
**Request:**
```http
GET /api/v1/safety/beach-status?zone_id=kolatoli&lang=en HTTP/1.1
Host: api.pothsathi.example
```

**Response (`200 OK`):**
```json
{
  "zones": [
    {
      "zone_id": "kolatoli",
      "zone_name": "Kolatoli Beach",
      "flag": "yellow",
      "flag_meaning": "Medium hazard. Rough surf or strong currents; swim with caution.",
      "last_updated": "2026-11-23T06:00:00Z",
      "updated_by": "EXAMPLE_admin_01",
      "is_outdated": false
    }
  ]
}
```

---

## 8 Module 7: Chat

AI assistant pipeline (safety rules, Gemini with tool calls, grounded answers, and RAG fallback) with multi-turn session persistence.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `POST /api/v1/chat/messages` | Authenticated (Tourist / Guest) | Body: `{ "message": string, "session_id"?: string, "language"?: "bn" or "en" }` | `200 OK`<br>`ChatResponse` | `400 INPUT_TOO_LONG`<br>`429 RATE_LIMITED`<br>`429 GEMINI_QUOTA`<br>`503 GEMINI_UNAVAILABLE` | `chat_sessions/{session_id}`, `chat_sessions/{session_id}/messages/{id}`, `usage/{uid_date}`, `ai_usage/{date}` |
| `GET /api/v1/chat/sessions` | Authenticated Tourist | Query: `limit`, `offset` | `200 OK`<br>`PaginatedList<ChatSession>` | `401 INVALID_TOKEN` | `chat_sessions/{session_id}` |
| `GET /api/v1/chat/sessions/{id}/messages` | Authenticated Tourist | Path: `id` (string)<br>Query: `limit`, `offset` | `200 OK`<br>`PaginatedList<ChatMessage>` | `401 INVALID_TOKEN`<br>`404 SESSION_NOT_FOUND` | `chat_sessions/{id}/messages/{msg_id}` |
| `DELETE /api/v1/chat/sessions/{id}` | Authenticated Tourist | Path: `id` (string) | `204 No Content` | `401 INVALID_TOKEN`<br>`404 SESSION_NOT_FOUND` | `chat_sessions/{id}` |

### Key Endpoint Example: `POST /api/v1/chat/messages`
**Request:**
```http
POST /api/v1/chat/messages HTTP/1.1
Host: api.pothsathi.example
Authorization: Bearer EXAMPLE_FIREBASE_ID_TOKEN
Content-Type: application/json

{
  "message": "কলাতলী বিচে ভালো হোটেল আছে ৩০০০ টাকার মধ্যে?",
  "session_id": "EXAMPLE_sess_001",
  "language": "bn"
}
```

**Response (`200 OK` - schema conforming to docs/ai-spec.md §12):**
```json
{
  "answer_text": "কলাতলী বিচ এলাকায় আপনার বাজেটের মধ্যে 'EXAMPLE_Sea_View' হোটেলটি পাওয়া গেছে। প্রতি রাতের ভাড়া আনুমানিক ২৫০০ টাকা।",
  "language": "bn",
  "cards": [
    {
      "type": "hotel",
      "data": {
        "hotel_id": "EXAMPLE_hotel_001",
        "name": "EXAMPLE_Sea_View",
        "area": "kolatoli",
        "price_min_bdt": 2500,
        "rating": 4.2
      }
    }
  ],
  "sources": [
    {
      "label": "Verified hotel data",
      "source_id": "hotels/EXAMPLE_hotel_001",
      "is_verified": true
    }
  ],
  "severity": null,
  "tool_calls_used": ["search_hotels"],
  "fallback_used": false,
  "safety_triggered": false,
  "is_ai_resting": false
}
```

---

## 9 Module 8: Emergency & SOS

Immediate emergency contacts and SOS alert logging with location for tourist safety.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/emergency/contacts` | Public / Guest | Query: `lang` | `200 OK`<br>`EmergencyContactList` | None | `places/{place_id}` |
| `POST /api/v1/emergency/sos` | Public / Guest | Body: `{ "lat"?: number, "lng"?: number, "trigger_type": "button" or "voice", "lang"?: "bn" or "en" }` | `201 Created`<br>`SOSResponse` | `400 INVALID_COORDINATES` | `sos_events/{id}` |

### Key Endpoint Example: `POST /api/v1/emergency/sos`
**Request:**
```http
POST /api/v1/emergency/sos HTTP/1.1
Host: api.pothsathi.example
Content-Type: application/json

{
  "lat": 21.4167,
  "lng": 91.9833,
  "trigger_type": "button",
  "lang": "en"
}
```

**Response (`201 Created`):**
```json
{
  "sos_id": "EXAMPLE_sos_101",
  "status": "logged",
  "national_emergency": "999",
  "tourist_police": "EXAMPLE_01700000001",
  "ambulance": "199",
  "guidance": "Please stay calm. Call 999 immediately. Share your location with nearby officials.",
  "quick_links": {
    "tel": "tel:999",
    "whatsapp": "https://wa.me/EXAMPLE_TOURIST_POLICE"
  }
}
```

---

## 10 Module 9: Reports

User submissions reporting incorrect, obsolete, or misleading data items (P1).

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `POST /api/v1/reports` | Public / Guest | Body: `{ "entity_type": "hotel", "place", or "transport_route", "entity_id": string, "issue_description": string, "reported_by_uid"?: string }` | `201 Created`<br>`ReportSubmissionResponse` | `400 INVALID_INPUT` | `reports/{id}` |

### Key Endpoint Example: `POST /api/v1/reports`
**Request:**
```http
POST /api/v1/reports HTTP/1.1
Host: api.pothsathi.example
Content-Type: application/json

{
  "entity_type": "hotel",
  "entity_id": "EXAMPLE_hotel_001",
  "issue_description": "The advertised swimming pool is currently under renovation."
}
```

**Response (`201 Created`):**
```json
{
  "report_id": "EXAMPLE_rep_555",
  "status": "pending",
  "message_en": "Thank you. Your report has been submitted for administrative review.",
  "message_bn": "ধন্যবাদ। আপনার প্রতিবেদনটি পর্যালোচনার জন্য জমা হয়েছে।"
}
```

---

## 11 Module 10: Admin (Role: Admin)

Administrative endpoints for managing master reference data, beach flags, cache invalidation, and monitoring metrics. All endpoints require `role == "admin"`.

### 11.1 Master Data CRUD
| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `POST /api/v1/admin/hotels` | Admin | Body: `HotelCreateSchema` | `201 Created`<br>`HotelDetail` | `400 INVALID_INPUT`<br>`403 FORBIDDEN` | `hotels/{id}`, `admin_audit/{id}` |
| `PUT /api/v1/admin/hotels/{id}` | Admin | Path: `id`<br>Body: `HotelUpdateSchema` | `200 OK`<br>`HotelDetail` | `400 INVALID_INPUT`<br>`404 NOT_FOUND` | `hotels/{id}`, `admin_audit/{id}` |
| `DELETE /api/v1/admin/hotels/{id}` | Admin | Path: `id` | `204 No Content` | `404 NOT_FOUND`<br>`403 FORBIDDEN` | `hotels/{id}`, `admin_audit/{id}` |
| `POST /api/v1/admin/places` | Admin | Body: `PlaceCreateSchema` | `201 Created`<br>`PlaceDetail` | `400 INVALID_INPUT`<br>`403 FORBIDDEN` | `places/{id}`, `admin_audit/{id}` |
| `PUT /api/v1/admin/places/{id}` | Admin | Path: `id`<br>Body: `PlaceUpdateSchema` | `200 OK`<br>`PlaceDetail` | `400 INVALID_INPUT`<br>`404 NOT_FOUND` | `places/{id}`, `admin_audit/{id}` |
| `DELETE /api/v1/admin/places/{id}` | Admin | Path: `id` | `204 No Content` | `404 NOT_FOUND`<br>`403 FORBIDDEN` | `places/{id}`, `admin_audit/{id}` |
| `POST /api/v1/admin/transport-routes` | Admin | Body: `RouteCreateSchema` | `201 Created`<br>`RouteDetail` | `400 INVALID_INPUT`<br>`403 FORBIDDEN` | `transport_routes/{id}`, `admin_audit/{id}` |
| `PUT /api/v1/admin/transport-routes/{id}` | Admin | Path: `id`<br>Body: `RouteUpdateSchema` | `200 OK`<br>`RouteDetail` | `400 INVALID_INPUT`<br>`404 NOT_FOUND` | `transport_routes/{id}`, `admin_audit/{id}` |
| `DELETE /api/v1/admin/transport-routes/{id}` | Admin | Path: `id` | `204 No Content` | `404 NOT_FOUND`<br>`403 FORBIDDEN` | `transport_routes/{id}`, `admin_audit/{id}` |
| `POST /api/v1/admin/kb-chunks` | Admin | Body: `ChunkCreateSchema` | `201 Created`<br>`KBChunkDetail` | `400 INVALID_INPUT`<br>`403 FORBIDDEN` | `kb_chunks/{id}`, `admin_audit/{id}` |
| `PUT /api/v1/admin/kb-chunks/{id}` | Admin | Path: `id`<br>Body: `ChunkUpdateSchema` | `200 OK`<br>`KBChunkDetail` | `400 INVALID_INPUT`<br>`404 NOT_FOUND` | `kb_chunks/{id}`, `admin_audit/{id}` |
| `DELETE /api/v1/admin/kb-chunks/{id}` | Admin | Path: `id` | `204 No Content` | `404 NOT_FOUND`<br>`403 FORBIDDEN` | `kb_chunks/{id}`, `admin_audit/{id}` |

### 11.2 Operational & Audit Endpoints
| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `PUT /api/v1/admin/beach-status/{zone_id}` | Admin | Path: `zone_id`<br>Body: `{ "flag": "green", "yellow", or "red", "flag_meaning": { "bn": string, "en": string } }` | `200 OK`<br>`BeachStatusRecord` | `400 INVALID_INPUT`<br>`403 FORBIDDEN` | `beach_status/{zone_id}`, `admin_audit/{id}` |
| `POST /api/v1/admin/cache/refresh` | Admin | Body: `{ "scope"?: "all", "hotels", "places", "fares", or "kb" }` | `200 OK`<br>`{ "status": "reloaded", "timestamp": string }` | `403 FORBIDDEN` | None (in-memory backend state) |
| `GET /api/v1/admin/stats` | Admin | None | `200 OK`<br>`AdminStatsResponse` | `403 FORBIDDEN` | `ai_usage/{date}`, `usage/{uid_date}`, `reports/{id}` |
| `GET /api/v1/admin/reports` | Admin | Query: `status` ("pending", "reviewed", or "all"?), `limit`, `offset` | `200 OK`<br>`PaginatedList<ReportItem>` | `403 FORBIDDEN` | `reports/{id}` |

### Key Endpoint Example: `PUT /api/v1/admin/beach-status/{zone_id}`
**Request:**
```http
PUT /api/v1/admin/beach-status/kolatoli HTTP/1.1
Host: api.pothsathi.example
Authorization: Bearer EXAMPLE_ADMIN_TOKEN
Content-Type: application/json

{
  "flag": "red",
  "flag_meaning": {
    "bn": "বিপদজনক পরিস্থিতি। সমুদ্রে নামা সম্পূর্ণ নিষেধ।",
    "en": "High hazard. Rough seas, swimming is strictly prohibited."
  }
}
```

**Response (`200 OK`):**
```json
{
  "zone_id": "kolatoli",
  "flag": "red",
  "last_updated": "2026-11-25T15:00:00Z",
  "updated_by": "EXAMPLE_admin_uid"
}
```

---

## 12 Module 11: Health & Diagnostics

Readiness, liveness, and keep-warm probe endpoint.

| Method & Path | Auth / Role | Parameters / Body | Response | Errors | Collections Touched |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/health` | Public | None | `200 OK`<br>`HealthCheckResponse` | `503 SERVICE_UNHEALTHY` | None (checks DB & AI connectivity) |

### Key Endpoint Example: `GET /api/v1/health`
**Request:**
```http
GET /api/v1/health HTTP/1.1
Host: api.pothsathi.example
```

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "environment": "prod",
  "rag_chunks": 58,
  "ai_quota_remaining": 358,
  "uptime_sec": 84120
}
```

---

## 13 Module 12: Later Endpoints (Names Only)

The following deferred capabilities are planned post-MVP and will not be implemented for the 9 December deadline:
1. `POST /api/v1/later/trip-plans` (Auto-generated day-by-day itinerary generator)
2. `POST /api/v1/later/translate/menu` (Optical character recognition and food menu translation)
3. `POST /api/v1/later/translate/photo` (Tourist sign photo translation)
4. `GET /api/v1/later/scams/heatmap` (Geographic scam report density map)
5. `GET /api/v1/later/pwa/sync` (Offline package delta sync for offline PWA operation)
6. `POST /api/v1/later/notifications/push` (Web push subscription for cyclone/tide alerts)
7. `GET /api/v1/later/owner/dashboard` (Hotel/restaurant owner self-serve claim and analytics)
8. `GET /api/v1/later/zones/extended` (Expansions covering Inani, Himchari, and Saint Martin)
9. `POST /api/v1/later/fares/checker` (Interactive fare fairness grader: fair, high, or too high)


---

## 14 Error Code Catalog

Unified catalog of application error codes, corresponding HTTP status codes, meanings, and localized user-facing messages.

| Error Code | HTTP Status | Meaning | message_bn | message_en |
| --- | --- | --- | --- | --- |
| `INVALID_INPUT` | `400 Bad Request` | Missing required payload field or validation error | অনুরোধের তথ্য সঠিক নয়। অনুগ্রহ করে তথ্য পরীক্ষা করুন। | Invalid request data. Please check your input. |
| `INPUT_TOO_LONG` | `400 Bad Request` | Chat prompt or input text exceeds 2,000 characters | বার্তাটি অনেক বড়। অনুগ্রহ করে ২০০০ অক্ষরের মধ্যে লিখুন। | Message is too long. Please keep it under 2,000 characters. |
| `INVALID_COORDINATES` | `400 Bad Request` | Latitude or longitude is out of bounds or missing | সঠিক ভৌগোলিক অবস্থান পাওয়া যায়নি। | Invalid geographical coordinates provided. |
| `INVALID_QUERY_PARAM` | `400 Bad Request` | Filter parameter or sort key not recognized | অনুরোধের ফিল্টারটি সঠিক নয়। | The query parameter or filter provided is invalid. |
| `INVALID_TOKEN` | `401 Unauthorized` | Missing, expired, or malformed Firebase ID token | লগইন সেশন মেয়াদোত্তীর্ণ বা অবৈধ। আবার লগইন করুন। | Login session expired or invalid. Please sign in again. |
| `FORBIDDEN` | `403 Forbidden` | Authenticated user lacks admin role privileges | এই কাজটি করার জন্য প্রশাসনিক অনুমতি নেই। | Administrative permissions required for this action. |
| `USER_NOT_FOUND` | `404 Not Found` | Target user profile does not exist in Firestore | ব্যবহারকারীর প্রোফাইল পাওয়া যায়নি। | User profile could not be found. |
| `HOTEL_NOT_FOUND` | `404 Not Found` | Requested hotel ID does not exist | হোটেলটি খুঁজে পাওয়া যায়নি। | The requested hotel could not be found. |
| `ROUTE_NOT_FOUND` | `404 Not Found` | Transport route between given zones is not mapped | এই রুটের নির্ধারিত ভাড়ার তথ্য পাওয়া যায়নি। | No verified fare route found for the given endpoints. |
| `SESSION_NOT_FOUND` | `404 Not Found` | Chat session ID does not exist or expired (>30 days) | চ্যাট সেশনটি আর সক্রিয় নেই। | Chat session not found or has expired. |
| `NOT_FOUND` | `404 Not Found` | Generic resource does not exist | কাঙ্ক্ষিত তথ্য খুঁজে পাওয়া যায়নি। | The requested resource was not found. |
| `RATE_LIMITED` | `429 Too Many Requests` | User daily quota (50 msgs) or IP rate limit exceeded | আজকের জন্য আপনার অনুরোধের সীমা শেষ। কাল আবার চেষ্টা করুন। | You have reached the rate limit. Please try again later. |
| `GEMINI_QUOTA` | `429 Too Many Requests` | Global daily AI budget exhausted ("AI rest mode") | আমাদের এআই সহকারী বিশ্রাম নিচ্ছে। নিচে সরাসরি তথ্য দেখুন। | AI assistant is resting. Please browse the verified guide below. |
| `INTERNAL_SERVER_ERROR` | `500 Internal Error` | Unhandled backend exception | সার্ভারে অপ্রত্যাশিত ত্রুটি ঘটেছে। কিছুক্ষণ পর চেষ্টা করুন। | An unexpected internal error occurred. Please try again later. |
| `GEMINI_UNAVAILABLE` | `503 Service Unavailable` | Downstream Gemini API outage or timeout | এআই সহকারী সাময়িকভাবে অনুপলব্ধ। দ্রুত ফিরে আসবে। | AI assistant is temporarily unavailable. Returning shortly. |
| `DB_UNAVAILABLE` | `503 Service Unavailable` | Cloud Firestore unreachable (triggers Tier 0 fallback) | ডেটাবেজ সেবা সাময়িকভাবে অনুপলব্ধ। প্রাথমিক তথ্য দেখানো হচ্ছে। | Database service unavailable. Showing offline reference data. |
| `SERVICE_UNHEALTHY` | `503 Service Unavailable` | Health probe failed critical component checks | পরিষেবাটিতে সমস্যা দেখা দিয়েছে। প্রযুক্তিগত কাজ চলছে। | Service failed health probe. Maintenance in progress. |

---

## 15 Endpoint Summary Table

Master inventory of all P0, P1, and P2 endpoints across modules.

| Method | Path | Auth / Role | Module | Priority |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Authenticated (Any) | Auth & Profile | P0 |
| `GET` | `/api/v1/me` | Authenticated (Any) | Auth & Profile | P0 |
| `PATCH` | `/api/v1/me` | Authenticated (Any) | Auth & Profile | P0 |
| `DELETE` | `/api/v1/me` | Authenticated (Any) | Auth & Profile | P0 |
| `GET` | `/api/v1/hotels` | Public / Guest | Hotels | P0 |
| `GET` | `/api/v1/hotels/{id}` | Public / Guest | Hotels | P0 |
| `GET` | `/api/v1/hotels/{id}/reviews` | Public / Guest | Reviews | P1 |
| `POST` | `/api/v1/hotels/{id}/reviews` | Authenticated Tourist | Reviews | P1 |
| `GET` | `/api/v1/nearby` | Public / Guest | Nearby Essentials | P0 |
| `GET` | `/api/v1/transport/fares` | Public / Guest | Transport & Fares | P0 |
| `GET` | `/api/v1/transport/calculate` | Public / Guest | Transport & Fares | P0 |
| `GET` | `/api/v1/safety/beach-status` | Public / Guest | Safety & Advisories | P0 |
| `GET` | `/api/v1/safety/advisories` | Public / Guest | Safety & Advisories | P0 |
| `POST` | `/api/v1/chat/messages` | Authenticated (Tourist / Guest) | Chat | P0 |
| `GET` | `/api/v1/chat/sessions` | Authenticated Tourist | Chat | P0 |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | Authenticated Tourist | Chat | P0 |
| `DELETE` | `/api/v1/chat/sessions/{id}` | Authenticated Tourist | Chat | P0 |
| `GET` | `/api/v1/emergency/contacts` | Public / Guest | Emergency & SOS | P0 |
| `POST` | `/api/v1/emergency/sos` | Public / Guest | Emergency & SOS | P0 |
| `POST` | `/api/v1/reports` | Public / Guest | Reports | P1 |
| `POST` | `/api/v1/admin/hotels` | Admin | Admin Data CRUD | P1 |
| `PUT` | `/api/v1/admin/hotels/{id}` | Admin | Admin Data CRUD | P1 |
| `DELETE` | `/api/v1/admin/hotels/{id}` | Admin | Admin Data CRUD | P1 |
| `POST` | `/api/v1/admin/places` | Admin | Admin Data CRUD | P1 |
| `PUT` | `/api/v1/admin/places/{id}` | Admin | Admin Data CRUD | P1 |
| `DELETE` | `/api/v1/admin/places/{id}` | Admin | Admin Data CRUD | P1 |
| `POST` | `/api/v1/admin/transport-routes` | Admin | Admin Data CRUD | P1 |
| `PUT` | `/api/v1/admin/transport-routes/{id}` | Admin | Admin Data CRUD | P1 |
| `DELETE` | `/api/v1/admin/transport-routes/{id}` | Admin | Admin Data CRUD | P1 |
| `POST` | `/api/v1/admin/kb-chunks` | Admin | Admin Data CRUD | P1 |
| `PUT` | `/api/v1/admin/kb-chunks/{id}` | Admin | Admin Data CRUD | P1 |
| `DELETE` | `/api/v1/admin/kb-chunks/{id}` | Admin | Admin Data CRUD | P1 |
| `PUT` | `/api/v1/admin/beach-status/{zone_id}` | Admin | Admin Operations | P1 |
| `POST` | `/api/v1/admin/cache/refresh` | Admin | Admin Operations | P1 |
| `GET` | `/api/v1/admin/stats` | Admin | Admin Operations | P1 |
| `GET` | `/api/v1/admin/reports` | Admin | Admin Operations | P1 |
| `GET` | `/api/v1/health` | Public | Health & Diagnostics | P0 |

---

## 16 Endpoint Name Mapping & Changes

The table below catalogs every endpoint name referenced in earlier documentation (`README.md`, `architecture.md`, `repo-structure.md`) alongside the standardized name in this specification, noting why each change was made.

| Earlier Doc Name | Spec Name in `api-spec.md` | Document Source | Rationale for Change |
| --- | --- | --- | --- |
| `/api/{resource}` | `/api/v1/{resource}` | `architecture.md` | Standardized on `/api/v1/` versioned prefix (as recommended in `repo-structure.md` Open Question 1) for backward compatibility. |
| `POST /api/chat` / `POST /api/v1/chat` | `POST /api/v1/chat/messages` | `architecture.md`, `repo-structure.md` | Shifted to standard REST resource convention `chat/messages` to support multi-turn session queries (`GET /chat/sessions`, `GET /chat/sessions/{id}/messages`). |
| `GET /api/fares` / `GET /api/v1/fares` | `GET /api/v1/transport/fares` | `architecture.md`, `repo-structure.md` | Aligned router prefix with `transport_service` and Firestore collection `transport_routes` as requested in task spec. |
| `POST /api/v1/fares/calculate` | `GET /api/v1/transport/calculate` | `repo-structure.md` | Fare calculation is an idempotent, side-effect-free mathematical query with query parameters. `GET` enables standard HTTP caching. |
| `POST /api/v1/auth/login` | `POST /api/v1/auth/register` & `GET /api/v1/me` | `repo-structure.md`, `architecture.md` | Authentication token verification happens in Firebase client-side SDK. The backend endpoint registers or syncs user profile docs in Firestore upon first sign-in. |
| `GET /api/emergency` / `GET /api/v1/emergency` | `GET /api/v1/emergency/contacts` | `architecture.md`, `repo-structure.md` | Clarified specific resource retrieved (emergency contact directory) to distinguish from SOS action endpoint. |
| `GET /api/safety` / `GET /api/v1/safety` | `GET /api/v1/safety/beach-status` & `GET /api/v1/safety/advisories` | `architecture.md` | Split root safety namespace into concrete sub-resources for live beach flag state and safety advisory texts. |

---

## 17 Open Questions & Assumptions

### 17.1 Assumptions
1. **Firebase Anonymous UID Persistence:** Guests browsing the website will obtain an anonymous session via Firebase Anonymous Auth on the frontend. This UID allows anonymous users to chat within the per-user 50 message/day cap without needing Google OAuth upfront.
2. **Review Permissions (P1):** Unauthenticated guests may read reviews, but posting a review (`POST /hotels/{id}/reviews`) requires an authenticated user token (tourist role).
3. **Admin Role Assignment:** Admin status is not self-assignable via API. It must be manually seeded or updated in Cloud Firestore `users/{uid}` document (`role: "admin"`).
4. **Calculations Caching:** `GET /transport/calculate` results are cached in backend memory with a 1-hour TTL based on route ID and passenger count.

### 17.2 Open Questions
1. **Transport Collection and Endpoint Naming Consistency:** Resolved per D22 and D25: standardized on `transport_routes` and `/api/v1/transport/*` across all documents.
2. **Keep-Warm Endpoint Authorization:** `GET /api/v1/health` is configured as a public endpoint without auth so external monitors (e.g. UptimeRobot) can ping it every 14 minutes. Should internal diagnostic metrics (`rag_chunks`, `ai_quota_remaining`) be masked or protected behind a secret query token in production?
3. **Session Retention Cleanup:** Chat sessions are specified to be retained for at most 30 days (D14). Does a nightly background worker clean up expired subcollections, or will TTL policies in Firestore be used? (Firestore TTL requires native mode and field policy).
